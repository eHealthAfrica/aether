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

import sys
from importlib import reload, import_module

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse, resolve, exceptions, clear_url_caches


class UrlsTestCase(TestCase):

    def setUp(self):
        reload(sys.modules[settings.ROOT_URLCONF])
        import_module(settings.ROOT_URLCONF)
        clear_url_caches()

    def tearDown(self):
        clear_url_caches()


@override_settings(KEYCLOAK_SERVER_URL=None)
class UrlsTest(UrlsTestCase):

    def test__urls__checks(self):
        self.assertEqual(reverse('health'), '/health')
        self.assertEqual(reverse('check-db'), '/check-db')
        self.assertEqual(reverse('check-app'), '/check-app')
        self.assertEqual(reverse('check-kernel'), '/check-kernel')
        self.assertEqual(reverse('admin:index'), '/admin/')

    def test__urls__accounts(self):
        self.assertEqual(reverse('rest_framework:login'), '/accounts/login/')
        self.assertEqual(reverse('rest_framework:logout'), '/accounts/logout/')
        self.assertEqual(reverse('rest_framework:token'), '/accounts/token')

    def test__urls__accounts__views(self):
        from django.contrib.auth import views

        self.assertEqual(resolve('/accounts/login/').func.view_class,
                         views.LoginView.as_view().view_class)
        self.assertEqual(resolve('/accounts/logout/').func.view_class,
                         views.LogoutView.as_view().view_class)


@override_settings(APP_URL='/aether')
class UrlsAppUrlTest(UrlsTestCase):

    def test__urls__checks(self):
        self.assertEqual(reverse('health'), '/aether/health')
        self.assertEqual(reverse('check-db'), '/aether/check-db')
        self.assertEqual(reverse('check-app'), '/aether/check-app')
        self.assertEqual(reverse('check-kernel'), '/aether/check-kernel')
        self.assertEqual(reverse('admin:index'), '/aether/admin/')

    def test__urls__accounts(self):
        self.assertEqual(reverse('rest_framework:login'), '/aether/accounts/login/')
        self.assertEqual(reverse('rest_framework:logout'), '/aether/accounts/logout/')
        self.assertEqual(reverse('rest_framework:token'), '/aether/accounts/token')


@override_settings(TEST_KERNEL_ACTIVE=False)
class UrlsNoKernelTest(UrlsTestCase):

    def test__urls__checks(self):
        self.assertRaises(exceptions.NoReverseMatch, reverse, 'check-kernel')


@override_settings(TEST_TOKEN_ACTIVE=False)
class UrlsNoTokenTest(UrlsTestCase):

    def test__urls__accounts(self):
        self.assertRaises(exceptions.NoReverseMatch, reverse, 'rest_framework:token')


@override_settings(
    CAS_SERVER_URL='http://localhost:6666',
    INSTALLED_APPS=[*settings.INSTALLED_APPS, 'django_cas_ng'],
)
class UrlsCASServerTest(UrlsTestCase):

    def test__urls__accounts(self):
        from django_cas_ng import views

        self.assertEqual(reverse('rest_framework:login'), '/accounts/login/')
        self.assertEqual(reverse('rest_framework:logout'), '/accounts/logout/')

        self.assertEqual(resolve('/accounts/login/').func, views.login)
        self.assertEqual(resolve('/accounts/logout/').func, views.logout)


@override_settings(KEYCLOAK_SERVER_URL='http://localhost:6666')
class UrlsKeycloakServerTest(UrlsTestCase):

    def test__urls__accounts__login(self):
        from aether.common.keycloak.views import KeycloakLoginView

        self.assertEqual(reverse('rest_framework:login'), '/accounts/login/')
        self.assertEqual(resolve('/accounts/login/').func.view_class,
                         KeycloakLoginView.as_view().view_class)
