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

import requests

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.translation import ugettext as _


class Command(BaseCommand):

    help = _('Register module in Kong')

    def handle(self, *args, **options):

        ssl_header = settings.SECURE_PROXY_SSL_HEADER
        scheme = ssl_header[1] if ssl_header else 'http'

        HOST_URL = settings.BASE_HOST  # External URL for host
        KONG_URL = f'{scheme}://{settings.KONG_INTERNAL}/'

        CLIENT_URL = settings.APP_INTERNAL
        CLIENT_NAME = settings.APP_ID

        PLUGIN_URL = f'{KONG_URL}services/{CLIENT_NAME}/plugins'
        ROUTE_URL = f'{KONG_URL}services/{CLIENT_NAME}/routes'

        # Register Client with Kong
        # Single API Service

        self.stdout.write(
            _('Exposing Service {name} @ {url}').format(name=CLIENT_NAME, url=CLIENT_URL)
        )

        data = {
            'name': f'{CLIENT_NAME}',
            'url': f'{CLIENT_URL}'
        }
        res = requests.post(f'{KONG_URL}services/', data=data)
        try:
            res.raise_for_status()

            api_id = res.json()['id']
            if api_id != settings.APP_ID:
                self.stdout.write(str(res.json()))
        except Exception:
            self.stderr.write(str(res.json()))

        # Routes
        # # protected Routes
        # # EVERYTHING past / will be JWT controlled

        data = {
            'paths': [f'/{CLIENT_NAME}'],
            'strip_path': 'false',
        }
        res = requests.post(ROUTE_URL, data=data)
        try:
            res.raise_for_status()
        except Exception:
            self.stderr.write(str(res.json()))

        route_info = res.json()
        protected_route_id = route_info['id']

        # Add a separate Path for static assets, which we will NOT protect

        data = {
            'paths': [f'/{CLIENT_NAME}/static'],
            'strip_path': 'false',
        }
        res = requests.post(ROUTE_URL, data=data)
        try:
            res.raise_for_status()
        except Exception:
            self.stderr.write(str(res.json()))

        # Add JWT Plugin to protected route.

        ROUTE_URL = f'{KONG_URL}routes/{protected_route_id}/plugins'
        data = {
            'name': 'jwt',
            'config.cookie_names': ['aether-jwt']
        }
        res = requests.post(ROUTE_URL, data=data)
        try:
            res.raise_for_status()
        except Exception:
            self.stderr.write(str(res.json()))

        # ADD CORS Plugin to Kong for all localhost requests

        data = {
            'name': 'cors',
            'config.origins': f'{scheme}://{HOST_URL}/*',
            'config.methods': 'GET, POST, DELETE, HEAD, PUT',
            'config.headers': 'Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, Authorization',
            'config.exposed_headers': 'Authorization',
            'config.max_age': 3600,
            'config.credentials': 'true',
        }
        res = requests.post(PLUGIN_URL, data=data)
        try:
            res.raise_for_status()
        except Exception:
            self.stderr.write(str(res.json()))

        self.stdout.write(
            _('Service {name} from, {url} now being served by kong @ /{name}.')
            .format(name=CLIENT_NAME, url=CLIENT_URL)
        )
