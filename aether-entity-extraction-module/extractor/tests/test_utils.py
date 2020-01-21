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

import fakeredis
import json
import requests

from unittest import TestCase, mock

from ..settings import KERNEL_URL
from ..utils import kernel_data_request, remove_from_redis, KERNEL_ARTEFACT_NAMES

from . import TENANT, MAPPINGSET


class UtilsTests(TestCase):

    @mock.patch('extractor.utils.request')
    def test_kernel_request__raise_for_status(self, mock_request):
        mock_response = requests.Response()
        mock_response.status_code = 400
        mock_request.return_value = mock_response

        with self.assertRaises(Exception) as e:
            kernel_data_request('test-url/', realm=TENANT)
            self.assertTrue('400 Client Error' in str(e.exception))

        mock_request.assert_has_calls([
            mock.call(
                url=f'{KERNEL_URL}/test-url/',
                method='get',
                json={},
                headers={
                    'Authorization': mock.ANY,
                    'aether-realm': TENANT,
                },
            ),
        ])

    @mock.patch('extractor.utils.request')
    def test_kernel_request(self, mock_request):
        mock_response = requests.Response()
        mock_response.status_code, mock_response.encoding, mock_response._content = 200, 'utf8', b'{"key": "a"}'
        mock_request.return_value = mock_response

        res = kernel_data_request('test-url/', realm=TENANT)
        self.assertEqual(res, {'key': 'a'})

    def test_remove_from_redis(self):
        redis = fakeredis.FakeStrictRedis()
        _key = f'_{KERNEL_ARTEFACT_NAMES.mappingsets}:{TENANT}:{MAPPINGSET["id"]}'

        redis.set(_key, json.dumps(MAPPINGSET))
        self.assertIsNotNone(redis.get(_key))

        remove_from_redis(MAPPINGSET['id'], KERNEL_ARTEFACT_NAMES.mappingsets, TENANT, redis)
        self.assertIsNone(redis.get(_key))
