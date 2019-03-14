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

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from .constants import SURVEYOR_GROUP_NAME


def get_surveyor_group():
    group, _ = Group.objects.get_or_create(name=SURVEYOR_GROUP_NAME)
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
                           .filter(groups__name=SURVEYOR_GROUP_NAME) \
                           .order_by('username')
