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

from django.test import TestCase
from django.urls import reverse


class UtilsTest(TestCase):

    def test__urls__health(self):
        self.assertEqual(
            reverse('health'),
            '/health',
            'There is a "/health" endpoint'
        )

    def test__urls__accounts_login(self):
        self.assertEqual(
            reverse('rest_framework:login'), '/accounts/login/',
            'There is a "/accounts/login/" endpoint'
        )

    def test__urls__accounts_logout(self):
        self.assertEqual(
            reverse('rest_framework:logout'), '/accounts/logout/',
            'There is a "/accounts/logout/" endpoint'
        )

    def test__urls__accounts_token(self):
        self.assertEqual(
            reverse('token'),
            '/accounts/token',
            'There is a "/accounts/token" endpoint'
        )

    def test__urls__check_core(self):
        self.assertEqual(
            reverse('check-kernel'),
            '/check-kernel',
            'There is a "/check-kernel" endpoint'
        )

    def test__urls__media(self):
        self.assertEqual(
            reverse('media', kwargs={'path': 'path/to/somewhere'}),
            '/media/path/to/somewhere',
            'There is a "/media" endpoint'
        )

    def test__urls__media_basic(self):
        self.assertEqual(
            reverse('media-basic', kwargs={'path': 'path/to/somewhere'}),
            '/media-basic/path/to/somewhere',
            'There is a "/media-basic" endpoint'
        )
