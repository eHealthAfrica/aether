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

from django.test import RequestFactory, TestCase, override_settings

from ..context_processors import aether_context


class ContextProcessorsTests(TestCase):

    def test_aether_context(self):
        request = RequestFactory().get('/')
        context = aether_context(request)

        self.assertFalse(context['dev_mode'])

        self.assertEqual(context['app_id'], 'aether')
        self.assertEqual(context['app_name'], 'aether-test')
        self.assertEqual(context['app_link'], 'http://aether-link-test')
        self.assertNotEqual(context['app_version'], '#.#.#')
        self.assertNotEqual(context['app_revision'], '---')

    @override_settings(
        KEYCLOAK_URL='http://0.0.0.0:8080',
        BASE_HOST='http://localhost',
        URL_ID='testing',
        DEFAULT_REALM='aether-testing',
    )
    def test_aether_context__with_keycloak(self):
        request = RequestFactory().get('/')

        self.assertEqual(
            aether_context(request)['jwt_login'],
            'http://localhost/auth/user/aether-testing/refresh?redirect=http://testserver/testing',
        )
