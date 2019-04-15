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

import mock

from django.test import TestCase, RequestFactory

from .. import utils
from . import MockResponse


class UtilsTests(TestCase):

    def test__json_prettified_simple(self):
        data = {}
        expected = '<pre><span></span><span class="p">{}</span>\n</pre>'

        pretty = str(utils.json_prettified(data))
        self.assertIn(expected, pretty)

    # check that the custom request method tries to execute at least three
    # times before failing
    def test__request__once(self):
        with mock.patch('aether.common.utils.requests.request',
                        return_value='ok') as mock_req_args:
            resp_args = utils.request('no matter what')
            self.assertEqual(resp_args, 'ok')
            mock_req_args.assert_called_once_with('no matter what')

        with mock.patch('aether.common.utils.requests.request',
                        return_value='ok') as mock_req_kwargs:
            resp_kwargs = utils.request(url='localhost', method='get')
            self.assertEqual(resp_kwargs, 'ok')
            mock_req_kwargs.assert_called_once_with(url='localhost', method='get')

    def test__request__twice(self):
        with mock.patch('aether.common.utils.requests.request',
                        side_effect=[Exception, 'ok']) as mock_req:
            response = utils.request(url='trying twice')
            self.assertEqual(response, 'ok')
            self.assertEqual(mock_req.call_count, 2)
            mock_req.assert_has_calls([
                mock.call(url='trying twice'),
                mock.call(url='trying twice'),
            ])

    def test__request__3_times(self):
        with mock.patch('aether.common.utils.requests.request',
                        side_effect=[Exception, Exception, 'ok']) as mock_req:
            response = utils.request(url='trying three times')
            self.assertEqual(response, 'ok')
            self.assertEqual(mock_req.call_count, 3)
            mock_req.assert_has_calls([
                mock.call(url='trying three times'),
                mock.call(url='trying three times'),
                mock.call(url='trying three times'),
            ])

    def test__request__3_times__raises(self):
        with mock.patch('aether.common.utils.requests.request',
                        side_effect=[
                            Exception('1'),
                            Exception('2'),
                            Exception('3'),
                            'ok',
                        ]) as mock_req:
            with self.assertRaises(Exception) as e:
                response = utils.request(url='raises exception')
                self.assertIsNone(response)
                self.assertIsNotNone(e)
                self.assertEqual(str(e), '3')

            self.assertEqual(mock_req.call_count, 3)

    def test__get_all_docs(self):

        def my_side_effect(*args, **kwargs):
            self.assertEqual(kwargs['method'], 'get')
            if kwargs['url'] == 'http://first':
                return MockResponse(json_data={'results': [2], 'next': 'http://next'})
            else:
                return MockResponse(json_data={'results': [1], 'next': None})

        with mock.patch('aether.common.utils.request', side_effect=my_side_effect) as mock_get:
            iterable = utils.get_all_docs('http://first', headers={})

            self.assertEqual(next(iterable), 2)
            self.assertEqual(next(iterable), 1)
            self.assertRaises(StopIteration, next, iterable)

            mock_get.assert_has_calls([
                mock.call(
                    method='get',
                    url='http://first',
                    headers={},
                ),
                mock.call(
                    method='get',
                    url='http://next',
                    headers={},
                ),
            ])

    def test__find_in_request(self):
        request = RequestFactory().get('/')
        key = 'my-key'

        self.assertIsNone(utils.find_in_request(request, key))

        request.META['HTTP_MY_KEY'] = 'in-headers'
        self.assertEqual(utils.find_in_request(request, key), 'in-headers')

        request.COOKIES[key] = 'in-cookies'
        self.assertEqual(utils.find_in_request(request, key), 'in-cookies')

        setattr(request, 'session', {})
        request.session[key] = 'in-session'
        self.assertEqual(utils.find_in_request(request, key), 'in-session')
