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
from django.contrib.auth.models import Group
from django.db.models import F


def get_multitenancy_model():
    '''
    Returns the ``settings.MULTITENANCY_MODEL`` class.
    '''

    (app_label, model_name) = settings.MULTITENANCY_MODEL.split('.')
    return apps.get_model(app_label, model_name, require_ready=True)


def get_current_realm(request):
    '''
    Finds the current realm within the cookies or within the request headers.

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


def filter_by_realm(request, data, mt_field=None):
    '''
    Includes the realm filter in the given data object (Queryset or Manager)
    '''

    if not settings.MULTITENANCY:
        return data

    # only returns the instances linked to the current realm
    field = f'{mt_field}__mt__realm' if mt_field else 'mt__realm'
    realm = get_current_realm(request)
    return data.annotate(mt_realm=F(field)).filter(mt_realm=realm)


def add_current_realm_in_headers(request, headers={}):
    '''
    Includes the current realm in the headers
    '''

    if not settings.MULTITENANCY:
        return headers

    headers[settings.REALM_COOKIE] = get_current_realm(request)
    return headers


def add_instance_realm_in_headers(instance, headers={}):
    '''
    Includes the instance realm in the headers
    '''

    if not settings.MULTITENANCY:
        return headers

    headers[settings.REALM_COOKIE] = instance.get_realm()
    return headers


def get_auth_group(request):
    '''
    Returns the authorization group that represents the current realm.
    '''

    if not settings.MULTITENANCY:
        return None

    group, _ = Group.objects.get_or_create(name=get_current_realm(request))
    return group


def add_user_to_realm(request, user):
    '''
    Adds the current realm authorization group to the user groups.
    '''

    if not settings.MULTITENANCY:
        return

    user.groups.add(get_auth_group(request))


def remove_user_from_realm(request, user):
    '''
    Removes the current realm authorization group form the user groups.
    '''

    if not settings.MULTITENANCY:
        return

    user.groups.remove(get_auth_group(request))


def filter_users_by_realm(request, data):
    '''
    Includes the realm group filter in the given users data object (Queryset or Manager)
    '''

    if not settings.MULTITENANCY:
        return data

    # only returns the users linked to the current realm
    return data.filter(groups__name=get_auth_group(request).name)
