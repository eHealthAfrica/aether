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

import json
import requests
import os

# Kong info


def ENV(x): return os.environ.get(x)


HOST_URL = ENV('BASE_HOST')  # External URL for host
KONG_URL = f'http://{ENV("KONG_INTERNAL")}/'  # Internal Kong URL
CLIENT_URL = 'http://kernel:8000/'  # Internal service URL
CLIENT_NAME = ENV('APP_ID')
PLUGIN_URL = f'{KONG_URL}services/{CLIENT_NAME}/plugins'
ROUTE_URL = f'{KONG_URL}services/{CLIENT_NAME}/routes'
# Register Client with Kong
# Single API Service

print(f'Exposing Service {CLIENT_NAME} @ {CLIENT_URL}')

data = {
    'name': f'{CLIENT_NAME}',
    'url': f'{CLIENT_URL}'
}
res = requests.post(
    f'{KONG_URL}services/',
    data=data
)
api_details = res.json()
api_id = api_details['id']

# Routes
# # protected Routes
# # EVERYTHING past / will be JWT controlled

data = {
    'paths': [
        f'/{CLIENT_NAME}'
    ],
    'strip_path': 'false'
}
res = requests.post(
    ROUTE_URL,
    data=data
)

route_info = res.json()
protected_route_id = route_info['id']

# Add a seperate Path for static assets, which we will NOT protect

data = {
    'paths': [
        f'/{CLIENT_NAME}/static'
    ],
    'strip_path': 'false'
}
res = requests.post(
    ROUTE_URL,
    data=data
)

# Add JWT Plugin to protected route.

ROUTE_URL = f'{KONG_URL}routes/{protected_route_id}/plugins'
data = {
    'name': 'jwt',
    'config.cookie_names': ['aether-jwt']
}
res = requests.post(
    ROUTE_URL,
    data=data
)

# ADD CORS Plugin to Kong for all localhost requests

data = {
    'name': 'cors',
    'config.origins': f'http://{HOST_URL}/*',
    'config.methods': 'GET, POST, DELETE, HEAD, PUT',
    'config.headers': 'Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, Authorization',
    'config.exposed_headers': 'Authorization',
    'config.max_age': 3600,
    'config.credentials': 'true'
}

res = requests.post(PLUGIN_URL, data=data)
print(f'Service {CLIENT_NAME} from, {CLIENT_URL}'
      + f' now being served by kong @ /{CLIENT_NAME}.')
