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

from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import PrimaryKeyRelatedField, ModelSerializer

from .models import MtInstance


def is_accessible_by_realm(request, obj):
    if not settings.MULTITENANCY:
        return True

    # Object instance should have a method named `is_accessible`.
    if getattr(obj, 'is_accessible', None) is not None:
        realm = request.COOKIES.get(settings.REALM_COOKIE, 'default')
        return obj.is_accessible(realm)

    return True


def filter_by_realm(request, data, mt_field='mt'):
    if not settings.MULTITENANCY:
        return data

    # only returns the instances linked to the current realm
    realm = request.COOKIES.get(settings.REALM_COOKIE, 'default')
    return data.annotate(mt_realm=F(f'{mt_field}__realm')).filter(mt_realm=realm)


def assign_to_realm(request, instance):
    if not settings.MULTITENANCY:
        return False

    # assign to current realm
    realm = request.COOKIES.get(settings.REALM_COOKIE, 'default')
    try:
        instance.mt.realm = realm
        instance.mt.save()
    except ObjectDoesNotExist:
        MtInstance.objects.create(instance=instance, realm=realm)

    return True


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
        assign_to_realm(request, self)

    def is_accessible(self, realm):
        '''
        Check if the object "realm" is the current realm.
        '''

        try:
            return self.mt.realm == realm
        except ObjectDoesNotExist:
            return False

    class Meta:
        abstract = True


class MtModelSerializer(ModelSerializer):
    '''
    The ``settings.MULTITENANCY_MODEL`` serializer class must extend this one.
    '''

    def create(self, validated_data):
        instance = super(MtModelSerializer, self).create(validated_data)
        assign_to_realm(self.context['request'], instance)
        return instance


class MtPrimaryKeyRelatedField(PrimaryKeyRelatedField):
    mt_field = 'mt'

    def __init__(self, **kwargs):
        self.mt_field = kwargs.pop('mt_field', self.mt_field)
        super(MtPrimaryKeyRelatedField, self).__init__(**kwargs)

    def get_queryset(self):
        qs = super(MtPrimaryKeyRelatedField, self).get_queryset()
        qs = filter_by_realm(self.context['request'], qs, self.mt_field)
        return qs


class MtViewSetMixin(object):
    mt_field = 'mt'

    def get_queryset(self):
        qs = super(MtViewSetMixin, self).get_queryset()
        return filter_by_realm(self.request, qs, self.mt_field)
