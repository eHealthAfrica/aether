#!/usr/bin/env python

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

import os
import requests
import sys

from settings import HOST, KONG_URL


def __post(url, data):
    res = requests.post(url, data=data)
    try:
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(res.status_code)
        print(res.json())
        raise e


def register_app(name, url):
    # Register Client with Kong
    # Single API Service
    data = {
        'name':f'{name}',
        'url': f'{url}',
    }
    client_info = __post(url=f'{KONG_URL}services/', data=data)
    client_id = client_info['id']

    # ADD CORS Plugin to Kong for whole domain CORS
    PLUGIN_URL = f'{KONG_URL}services/{name}/plugins'
    data = {
        'name': 'cors',
        'config.origins': f'{HOST}/*',
        'config.methods': ['HEAD', 'GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
        'config.headers': 'Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, Authorization',
        'config.exposed_headers': 'Authorization',
        'config.max_age': 3600,
        'config.credentials': 'true',
    }
    __post(url=PLUGIN_URL, data=data)

    # Routes
    # Add a route which we will NOT protect
    ROUTE_URL = f'{KONG_URL}services/{name}/routes'
    data = {
        'paths' : [f'/{name}'],
        'strip_path': 'false',
        'preserve_host': 'false',  # This is keycloak specific.
    }
    __post(url=ROUTE_URL, data=data)

    return client_id


if __name__ == '__main__':
    CLIENT_NAME = sys.argv[1]
    CLIENT_URL = sys.argv[2]

    print(f'Exposing Service {CLIENT_NAME} @ {CLIENT_URL}')
    client_id = register_app(CLIENT_NAME, CLIENT_URL)
    print(f'Service {CLIENT_NAME} from {CLIENT_URL} now being served by kong @ /{client_id}.')
