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

from django.test import TestCase, override_settings

from aether.common.utils import resolve_file_url


class UtilsTest(TestCase):

    def test_resolve_file_url(self):
        absolute_url = 'http://test.com/test/'
        relative_url = '/test/'
        self.assertEqual(resolve_file_url(absolute_url), absolute_url)
        self.assertEqual(resolve_file_url(relative_url), 'http://example.com/test/')

    @override_settings(
        KEYCLOAK_URL='http://0.0.0.0:8080',
        BASE_HOST='http://localhost',
        APP_ID='testing',
    )
    def test_resolve_file_url__with_keycloak(self):
        absolute_url = 'http://test.com/test/'
        relative_url = '/test/'
        self.assertEqual(resolve_file_url(absolute_url), absolute_url)
        self.assertEqual(resolve_file_url(relative_url), 'http://localhost/testing/test/')
