# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Model, F
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import PrimaryKeyRelatedField, ModelSerializer

from .models import MtInstance


def get_current_realm(request):
    '''
    Find the current realm within the cookies or within the request headers.

    https://docs.djangoproject.com/en/2.1/ref/request-response/#django.http.HttpRequest.COOKIES
    https://docs.djangoproject.com/en/2.1/ref/request-response/#django.http.HttpRequest.META
    '''

    return getattr(request, 'COOKIES', {}).get(
        settings.REALM_COOKIE,
        getattr(request, 'META', {}).get(
            settings.REALM_HEADER,
            settings.DEFAULT_REALM
        )
    )


def is_accessible_by_realm(request, obj):
    '''
    Indicates if the instance is accessible by the current realm/tenant.
    '''

    if not settings.MULTITENANCY:
        return True

    # Object instance should have a method named `is_accessible`.
    if getattr(obj, 'is_accessible', None) is not None:
        realm = get_current_realm(request)
        return obj.is_accessible(realm)

    return True


def filter_by_realm(request, data, mt_field='mt'):
    '''
    Include the realm filter in the given data object (Queryset or Manager)
    '''

    if not settings.MULTITENANCY:
        return data

    # only returns the instances linked to the current realm
    realm = get_current_realm(request)
    return data.annotate(mt_realm=F(f'{mt_field}__realm')).filter(mt_realm=realm)


def assign_to_realm(request, instance):
    '''
    Assigns the intance the the current realm
    '''

    if not settings.MULTITENANCY:
        return False

    # assign to current realm
    realm = get_current_realm(request)
    try:
        instance.mt.realm = realm
        instance.mt.save()
    except ObjectDoesNotExist:
        MtInstance.objects.create(instance=instance, realm=realm)

    return True


def assign_current_realm_in_headers(request, headers={}):
    '''
    Includes the current realm in the headers
    '''

    if not settings.MULTITENANCY:
        return headers

    headers[settings.REALM_COOKIE] = get_current_realm(request)
    return headers


def assign_instance_realm_in_headers(instance, headers={}):
    '''
    Includes the instance realm in the headers
    '''

    if not settings.MULTITENANCY:
        return headers

    headers[settings.REALM_COOKIE] = instance.get_realm()
    return headers


class IsAccessibleByRealm(IsAuthenticated):
    '''
    Object-level permission to allow access to objects linked to the current realm.
    '''

    def has_object_permission(self, request, view, obj):
        return is_accessible_by_realm(request, obj)


def get_multitenancy_model():
    '''
    Returns the ``settings.MULTITENANCY_MODEL`` class.
    '''

    (app_name, model_name) = settings.MULTITENANCY_MODEL.split('.')
    return apps.get_app_config(app_name).get_model(model_name, require_ready=True)


class MtModelAbstract(Model):
    '''
    The ``settings.MULTITENANCY_MODEL`` class must extend this one.
    '''

    def save_mt(self, request):
        '''
        Assigns the instance to the current realm.
        '''

        assign_to_realm(request, self)

    def is_accessible(self, realm):
        '''
        Check if the object "realm" is the current realm.
        '''

        return settings.MULTITENANCY and self.get_realm() == realm

    def get_realm(self):
        '''
        Returns the object "realm" or the default one if missing.
        '''

        if not settings.MULTITENANCY:
            return None

        try:
            return self.mt.realm
        except ObjectDoesNotExist:
            return settings.DEFAULT_REALM

    class Meta:
        abstract = True


class MtModelSerializer(ModelSerializer):
    '''
    The ``settings.MULTITENANCY_MODEL`` serializer class must extend this one.
    '''

    def create(self, validated_data):
        '''
        Assigns the new instance to the current realm
        '''

        instance = super(MtModelSerializer, self).create(validated_data)
        instance.save_mt(self.context['request'])
        return instance


class MtPrimaryKeyRelatedField(PrimaryKeyRelatedField):
    '''
    Overrides `get_queryset` method to include filter by realm.
    Expects `mt_field` property.
    '''

    mt_field = 'mt'

    def __init__(self, **kwargs):
        self.mt_field = kwargs.pop('mt_field', self.mt_field)
        super(MtPrimaryKeyRelatedField, self).__init__(**kwargs)

    def get_queryset(self):
        '''
        Overrides `get_queryset` method to include filter by realm
        '''

        qs = super(MtPrimaryKeyRelatedField, self).get_queryset()
        qs = filter_by_realm(self.context['request'], qs, self.mt_field)
        return qs


class MtViewSetMixin(object):
    '''
    Overrides `get_queryset` method to include filter by realm.
    Expects `mt_field` property.

    Adds two new method:
        - `get_object_or_404(pk)` raises NO_FOUND error if the instacne is not accessible
        - `get_object_or_403(pk)` raises FORBIDDEN error if the instacne is not accessible
    '''

    mt_field = 'mt'

    def get_queryset(self):
        '''
        Overrides `get_queryset` method to include filter by realm in each query
        '''

        qs = super(MtViewSetMixin, self).get_queryset()
        return filter_by_realm(self.request, qs, self.mt_field)

    def get_object_or_404(self, pk):
        '''
        Custom method that raises NO_FOUND error
        if the instance that not exists
        or is not accessible by current realm
        otherwise return the instance
        '''

        return get_object_or_404(self.get_queryset(), pk=pk)

    def get_object_or_403(self, pk):
        '''
        Custom method that raises FORBIDDEN error
        if the instance is not accessible by current realm
        otherwise returns the instance or None if it does not exist
        '''

        # without filtering by realm
        qs = super(MtViewSetMixin, self).get_queryset()
        if not qs.filter(pk=pk).exists():
            return None

        obj = qs.get(pk=pk)
        if not is_accessible_by_realm(self.request, obj):
            raise PermissionDenied(_('Not accessible by this realm'))

        return obj
