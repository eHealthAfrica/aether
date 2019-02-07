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

import json
import os
import requests

get_env = lambda x : os.environ.get(x)

# Kong info
# TODO Make ENVs

HOST = get_env('BASE_HOST')  # External URL for host
KONG_URL = f'http://{get_env("KONG_INTERNAL")}/'  # available kong admin url

CLIENT_URL = f'http://{get_env("KEYCLOAK_INTERNAL")}/'  # internal service url
CLIENT_NAME = 'keycloak'

print(f'Exposing Service {CLIENT_NAME} @ {CLIENT_URL}')

# Register Client with Kong
# Single API Service

data = {
    'name':f'{CLIENT_NAME}',
    'url': f'{CLIENT_URL}',
}
res = requests.post(f'{KONG_URL}services/', data=data)
res.raise_for_status()

# Routes
# Add a route which we will NOT protect

ROUTE_URL = f'{KONG_URL}services/{CLIENT_NAME}/routes'
data = {
    'paths' : [f'/{CLIENT_NAME}'],
    'strip_path': 'false',
    'preserve_host': 'false',  # This is keycloak specific.
}
res = requests.post(ROUTE_URL, data=data)
res.raise_for_status()

# ADD CORS Plugin to Kong for whole domain CORS

PLUGIN_URL = f'{KONG_URL}services/{CLIENT_NAME}/plugins'
data = {
    'name': 'cors',
    'config.origins': f'http://{HOST}/*',
    'config.methods': ['HEAD', 'GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
    'config.headers': 'Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, Authorization',
    'config.exposed_headers': 'Authorization',
    'config.max_age': 3600,
    'config.credentials': 'true',
}
res = requests.post(PLUGIN_URL, data=data)
res.raise_for_status()

print(
    f'Service {CLIENT_NAME} from, {CLIENT_URL}'
    f' now being served by kong @ /{CLIENT_NAME}.'
)
