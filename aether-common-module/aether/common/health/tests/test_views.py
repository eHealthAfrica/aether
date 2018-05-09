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
# software distributed under the License is distributed on anx
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import mock

from django.urls import reverse
from django.test import TestCase

from rest_framework import status


class ViewsTest(TestCase):

    def test__health(self, *args):
        response = self.client.get(reverse('health'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {})

    @mock.patch('aether.common.health.views.test_db_connection', return_value=True)
    def test__check_db_ok(self, *args):
        response = self.client.get(reverse('check-db'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})

    @mock.patch('aether.common.health.views.test_db_connection', return_value=False)
    def test__check_db_down(self, *args):
        response = self.client.get(reverse('check-db'))
        self.assertEqual(response.status_code, 500)
