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

from django.conf import settings
from django.contrib.auth import get_user_model

from ..multitenancy.utils import get_current_realm, add_user_to_realm

UserModel = get_user_model()
user_objects = UserModel.objects


def get_or_create_user(request, username):

    realm = get_current_realm(request)

    # gets the existing user or creates a new one
    # the internal username prepends the realm name
    _username = f'{realm}__{username}' if settings.MULTITENANCY else username
    try:
        user = user_objects.get(username=_username)
    except UserModel.DoesNotExist:
        user = user_objects.create_user(
            username=_username,
            password=user_objects.make_random_password(length=100),
        )
    add_user_to_realm(request, user)

    return user
