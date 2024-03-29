# Copyright (C) 2023 by eHealth Africa : http://www.eHealthAfrica.org
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

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from aether.sdk.multitenancy.utils import get_auth_group, is_accessible_by_realm

from .models import Project, XForm, MediaFile


def get_surveyor_group():
    group, _ = Group.objects.get_or_create(name=settings.SURVEYOR_GROUP_NAME)
    return group


def get_surveyors():
    '''
    Extracts the list of valid surveyors from the users list.

    Conditions:
    - active users
    - have the group `surveyor`

    '''

    return get_user_model().objects \
                           .filter(is_active=True) \
                           .filter(groups__name=settings.SURVEYOR_GROUP_NAME) \
                           .order_by('username')


def is_surveyor(user):
    return get_surveyor_group() in user.groups.all()


def is_granted_surveyor(request, instance):
    '''
    Check that the user request is surveyor and is a granted surveyor of the instance:

    - If multitenancy is enabled:
        - User and instance must belong to the current realm.

    - If instance is a Project:
        - Project has no surveyors.
        - User is in the surveyors list.

    - If instance is an XForm:
        - xForm and Project have no surveyors.
        - User is in the xForm or Project surveyors list.

    - If instance is a Media File:
        - User is surveyor of the XForm
    '''

    group = get_auth_group(request)
    user = request.user

    if (
        not is_surveyor(user) or
        (group and group not in user.groups.all()) or
        not is_accessible_by_realm(request, instance)
    ):
        return False

    if isinstance(instance, Project):
        return (
            instance.surveyors.count() == 0 or
            user in instance.surveyors.all()
        )

    if isinstance(instance, XForm):
        return (
            (instance.surveyors.count() == 0 and instance.project.surveyors.count() == 0) or
            user in instance.surveyors.all() or
            user in instance.project.surveyors.all()
        )

    if isinstance(instance, MediaFile):
        return is_granted_surveyor(request, instance.xform)

    return False  # pragma: no cover
