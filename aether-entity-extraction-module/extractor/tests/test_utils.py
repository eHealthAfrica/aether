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
import requests

from unittest import TestCase, mock

from extractor.settings import (
    DEFAULT_REALM,
    KERNEL_TOKEN,
    KERNEL_URL,
    REALM_COOKIE,
)
from extractor.utils import (
    get_from_redis_or_kernel,
    get_redis_subscribed_message,
    kernel_data_request,
    remove_from_redis,
)


class UtilsTests(TestCase):

    @mock.patch('extractor.utils.request')
    def test_kernel_request__raise_for_status(self, mock_request):
        mock_response = requests.Response()
        mock_response.status_code = 400
        mock_request.return_value = mock_response

        with self.assertRaises(Exception) as e:
            kernel_data_request('test-url-400', realm='TENANT')
            self.assertTrue('400 Client Error' in str(e.exception))

        mock_request.assert_has_calls([
            mock.call(
                url=f'{KERNEL_URL}/test-url-400',
                method='get',
                json={},
                headers={
                    'Authorization': f'Token {KERNEL_TOKEN}',
                    REALM_COOKIE: 'TENANT',
                },
            ),
        ])

    @mock.patch('extractor.utils.request')
    def test_kernel_request(self, mock_request):
        mock_response = requests.Response()
        mock_response.status_code = 200
        mock_response.encoding = 'utf8'
        mock_response._content = b'{"key": "a"}'
        mock_request.return_value = mock_response

        res = kernel_data_request('test-url-ok')
        self.assertEqual(res, {'key': 'a'})

        mock_request.assert_has_calls([
            mock.call(
                url=f'{KERNEL_URL}/test-url-ok',
                method='get',
                json={},
                headers={
                    'Authorization': f'Token {KERNEL_TOKEN}',
                    REALM_COOKIE: DEFAULT_REALM,
                },
            ),
        ])

    def test_get_from_redis_or_kernel(self):
        redis = fakeredis.FakeStrictRedis()
        _key = '_model:tenant:id'
        self.assertIsNone(redis.get(_key))

        # not in redis or kernel
        with mock.patch(
            'extractor.utils.kernel_data_request',
            return_value=None
        ) as mocked_1:
            result = get_from_redis_or_kernel('id', 'model', 'tenant', redis)
            self.assertIsNone(result)
            self.assertIsNone(redis.get(_key))
            mocked_1.assert_called()

        with mock.patch(
            'extractor.utils.kernel_data_request',
            return_value={'id': 'id'}
        ) as mocked_2:
            result = get_from_redis_or_kernel('id', 'model', 'tenant', redis)
            self.assertEqual(result['id'], 'id')
            self.assertIn('modified', result, 'caching in redis adds modified')
            self.assertIsNotNone(redis.get(_key), 'cached in redis')
            mocked_2.assert_called()

        with mock.patch(
            'extractor.utils.kernel_data_request',
            return_value={'id': 'jd'}
        ) as mocked_3:
            result = get_from_redis_or_kernel('id', 'model', 'tenant', redis)
            self.assertEqual(result['id'], 'id')
            mocked_3.assert_not_called()

    def test_remove_from_redis(self):
        redis = fakeredis.FakeStrictRedis()
        _key = '_a:b:c'

        redis.set(_key, 'testing')
        self.assertEqual(redis.get(_key), b'testing')

        remove_from_redis('c', 'a', 'b', redis)
        self.assertIsNone(redis.get(_key))

    def get_redis_subscribed_message(self):
        server = fakeredis.FakeServer()
        server.connected = True
        redis = fakeredis.FakeStrictRedis(server=server)

        # wrong key format
        message = get_redis_subscribed_message('_s_b_c', redis)
        self.assertIsNone(message)

        _key = '_a:b:c'

        # not in redis yet
        message = get_redis_subscribed_message(_key, redis)
        self.assertIsNone(message)

        # in redis
        redis.set(_key, 'something')
        message = get_redis_subscribed_message(_key, redis)
        self.assertEqual(message, 'something')

        # server disconnected (exception)
        server.connected = False
        message = get_redis_subscribed_message(_key, redis)
        self.assertIsNone(message)
