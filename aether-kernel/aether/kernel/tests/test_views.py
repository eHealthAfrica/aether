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

from django.urls import reverse
from django.test import TestCase

from rest_framework import status


class TestViews(TestCase):

    def test__health_check(self):
        response = self.client.get(reverse('health'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {})

    def test_api_pass(self):
        response = self.client.post('/token', {'client_id': 'a_test_client_id'})
        self.assertEqual(400, response.status_code)
        response = self.client.post('/token', {'username': 'testUsername', 'password': 'testPassword'})
        self.assertEqual(200, response.status_code)
        response = self.client.post('/token',
                                    {'username': 'testUsername', 'password': 'testPassword',
                                     'redirect_uri': 'http://testuri.org', 'app_name': 'test_app'})
        self.assertEqual(200, response.status_code)

    def test__urls__api_pass(self):
        self.assertEqual(
            reverse('token'),
            '/token',
            'There is a "/token" endpoint'
        )
