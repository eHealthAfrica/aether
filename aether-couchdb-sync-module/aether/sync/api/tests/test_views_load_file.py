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

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from aether.sync.api.tests import DEVICE_TEST_FILE


class LoadFileViewsTests(TestCase):

    def setUp(self):
        super(LoadFileViewsTests, self).setUp()

        username = 'admin'
        email = 'admin@example.com'
        password = 'adminadmin'
        get_user_model().objects.create_superuser(username, email, password)
        self.assertTrue(self.client.login(username=username, password=password))

        self.url = reverse('load-file')

    def tearDown(self):
        super(LoadFileViewsTests, self).tearDown()
        self.client.logout()

    def test_register_url(self):
        self.assertTrue(self.url, 'The load file url is defined')
        self.assertEqual(self.url, '/sync/load-file')

    def test__load_file__without_file(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 400)

    @mock.patch('aether.sync.api.views.load_backup_file', return_value={'message': 'done'})
    def test__load_file__mocked(self, mock_load):
        with open(DEVICE_TEST_FILE, 'rb') as f:
            response = self.client.post(self.url, {'file': f})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {'message': 'done'})

        mock_load.assert_called_once()
