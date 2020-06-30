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

import requests

from datetime import datetime
from gevent import sleep

from aether.producer.settings import SETTINGS
from aether.producer.kernel import KernelClient, logger
from aether.producer.utils import utf8size

_REQUEST_ERROR_RETRIES = int(SETTINGS.get('request_error_retries', 3))

# Aether kernel
_KERNEL_TOKEN = SETTINGS.get_required('aether_kernel_token')
_KERNEL_URL = SETTINGS.get_required('aether_kernel_url')

# Multitenancy
_DEFAULT_REALM = SETTINGS.get('default_realm', 'eha')
_REALM_COOKIE = SETTINGS.get('realm_cookie', 'eha-realm')
_REALMS_PATH = SETTINGS.get('aether_kernel_realms_path', '/admin/~realms')

# Aether Kernel REST API urls
_REALMS_URL = f'{_KERNEL_URL}{_REALMS_PATH}'
_SCHEMAS_URL = (
    f'{_KERNEL_URL}/'
    'schemadecorators.json?'
    '&page_size={page_size}'
    '&fields=id,schema,schema_name,schema_definition'
)
_ENTITIES_SINGLE_URL = (
    f'{_KERNEL_URL}/'
    'entities.json?'
    '&page_size={page_size}'
    '&fields=id,modified,payload,schema'
    '&ordering=modified'
    '&modified__gt={modified}'
    '&schema={schema}'
)
_ENTITIES_ALL_URL = (
    f'{_KERNEL_URL}/'
    'entities.json?'
    '&page_size={page_size}'
    '&fields=id,modified,payload,schema'
    '&ordering=modified'
    '&modified__gt={modified}'
    '&schema={schema}'
)


class KernelAPIClient(KernelClient):

    def mode(self):
        return 'api'

    def get_realms(self):
        return self._fetch(url=_REALMS_URL)['realms']

    def get_schemas(self, realm=None):
        self.last_check = datetime.now().isoformat()

        try:
            # get list of realms
            if not realm:
                realms = self.get_realms()
            else:
                realms = [realm]
            for realm in realms:
                # get list of schema decorators
                _next_url = _SCHEMAS_URL.format(page_size=self.limit)
                while _next_url:
                    response = self._fetch(url=_next_url, realm=realm)
                    _next_url = response['next']

                    for entry in response['results']:
                        yield {'realm': realm, 'schema_id': entry['schema'], **entry}

        except Exception:
            self.last_check_error = 'Could not access kernel API to get topics'
            logger.warning(self.last_check_error)
            return []

    def check_updates(self, realm, schema_id=None, schema_name=None, modified=''):
        if schema_id:
            url = _ENTITIES_SINGLE_URL.format(
                page_size=1,
                schema=schema_id,
                modified=modified or '',
            )
        else:
            url = _ENTITIES_ALL_URL.format(
                page_size=1,
                modified=modified or '',
            )
        try:
            response = self._fetch(url=url, realm=realm)
            return response['count'] > 1
        except Exception:
            logger.warning('Could not access kernel API to look for updates')
            return False

    def count_updates(self, realm, schema_id=None, schema_name=None, modified=''):
        if schema_id:
            url = _ENTITIES_SINGLE_URL.format(
                page_size=1,
                schema=schema_id,
                modified=modified or '',
            )
        else:
            url = _ENTITIES_ALL_URL.format(
                page_size=1,
                modified=modified or '',
            )
        try:
            _count = self._fetch(url=url, realm=realm)['count']
            logger.debug(
                f'Reporting requested size for {schema_name or "all entities"} of {_count}')
            return {'count': _count}
        except Exception:
            logger.warning('Could not access kernel API to look for updates')
            return -1

    def get_updates(self, realm, schema_id=None, schema_name=None, modified=''):
        if schema_id:
            url = _ENTITIES_SINGLE_URL.format(
                page_size=self.limit,
                schema=schema_id,
                modified=modified or '',
            )
        else:
            url = _ENTITIES_ALL_URL.format(
                page_size=self.limit,
                modified=modified or '',
            )

        try:
            query_time = datetime.now()
            window_filter = self.get_time_window_filter(query_time)

            response = self._fetch(url=url, realm=realm)
            res = []
            size = 0
            for entry in response['results']:
                if window_filter(entry):
                    new_size = size + utf8size(entry)
                    res.append(entry)
                    if new_size >= self.batch_size:
                        # when we get over the batch size, truncate
                        # this means even with a batch size of 1, if a message
                        # is 10, we still emit one message
                        return res
                    size = new_size

            return res

        except Exception:
            logger.warning('Could not access kernel API to look for updates')
            return []

    def _fetch(self, url, realm=None):
        '''
        Executes the request call at least X times (``REQUEST_ERROR_RETRIES``)
        trying to avoid unexpected connection errors (not request expected ones).

        Like:
            # ConnectionResetError: [Errno 104] Connection reset by peer
            # http.client.RemoteDisconnected: Remote end closed connection without response
        '''

        headers = {
            'Authorization': f'Token {_KERNEL_TOKEN}',
            _REALM_COOKIE: realm if realm else _DEFAULT_REALM
        }

        count = 0
        while True:
            count += 1
            try:
                response = requests.get(url, headers=headers)
                return response.json()
            except Exception as e:
                if count >= _REQUEST_ERROR_RETRIES:
                    logger.warning(f'Error while fetching data from {url}')
                    logger.debug(e)
                    raise e
            sleep(count)  # sleep longer in each iteration
