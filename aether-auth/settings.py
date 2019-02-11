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

import os

get_env = lambda x : os.environ.get(x)


HOST = get_env('BASE_HOST')  # External URL for host
APP_NAME = get_env('APP_NAME')
APP_PORT = get_env('APP_PORT')


# Keycloak Information
KEYCLOAK_INTERNAL = get_env('KEYCLOAK_INTERNAL')
KEYCLOAK_URL = f'{HOST}/keycloak/auth/'

KC_URL = f'{KEYCLOAK_INTERNAL}/keycloak/auth/'  # internal
KC_ADMIN_USER = get_env('KEYCLOAK_GLOBAL_ADMIN')
KC_ADMIN_PASSWORD = get_env('KEYCLOAK_GLOBAL_PASSWORD')
KC_MASTER_REALM = 'master'


# Kong Information
KONG_URL = f'{get_env("KONG_INTERNAL")}/'
CONSUMERS_URL = f'{KONG_URL}consumers'


REALMS_PATH = '/code/realm'
JWT_COOKIE = get_env('JWT_COOKIE') or 'aether-jwt'
REALM_COOKIE = get_env('REALM_COOKIE') or 'aether-realm'
