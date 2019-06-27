# Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
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

from django_eha_sdk.health.utils import (
    check_external_app,
    get_external_app_url,
    get_external_app_token,
)

EXTERNAL_APP_KERNEL = 'aether-kernel'


def check_kernel_connection():
    return check_external_app(EXTERNAL_APP_KERNEL)


def get_kernel_url():
    return get_external_app_url(EXTERNAL_APP_KERNEL)


def get_kernel_auth_header():
    return {'Authorization': f'Token {get_external_app_token(EXTERNAL_APP_KERNEL)}'}
