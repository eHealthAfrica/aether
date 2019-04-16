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

from django.conf import settings
from django.test import override_settings
from django.urls import reverse, resolve, exceptions

from . import UrlsTestCase


@override_settings(
    KEYCLOAK_SERVER_URL=None,
    ADMIN_URL='admin',
    AUTH_URL='accounts',
)
class UrlsTest(UrlsTestCase):

    def test__urls__checks(self):
        self.assertEqual(reverse('health'), '/health')
        self.assertEqual(reverse('check-db'), '/check-db')
        self.assertEqual(reverse('check-app'), '/check-app')
        self.assertEqual(reverse('check-kernel'), '/check-kernel')
        self.assertEqual(reverse('admin:index'), '/admin/')

    def test__urls__auth(self):
        self.assertEqual(reverse('rest_framework:login'), '/accounts/login/')
        self.assertEqual(reverse('rest_framework:logout'), '/accounts/logout/')
        self.assertEqual(reverse('rest_framework:token'), '/accounts/token')
        self.assertEqual(reverse('logout'), '/logout/')

    def test__urls__auth__views(self):
        from django.contrib.auth.views import LoginView, LogoutView

        self.assertEqual(resolve('/accounts/login/').func.view_class,
                         LoginView.as_view().view_class)
        self.assertEqual(resolve('/accounts/logout/').func.view_class,
                         LogoutView.as_view().view_class)
        self.assertEqual(resolve('/logout/').func.view_class,
                         LogoutView.as_view().view_class)


@override_settings(
    APP_URL='/aether',
    ADMIN_URL='admin',
    AUTH_URL='accounts',
)
class UrlsAppUrlTest(UrlsTestCase):

    def test__urls__checks(self):
        self.assertEqual(reverse('health'), '/aether/health')
        self.assertEqual(reverse('check-db'), '/aether/check-db')
        self.assertEqual(reverse('check-app'), '/aether/check-app')
        self.assertEqual(reverse('check-kernel'), '/aether/check-kernel')
        self.assertEqual(reverse('admin:index'), '/aether/admin/')

    def test__urls__auth(self):
        self.assertEqual(reverse('rest_framework:login'), '/aether/accounts/login/')
        self.assertEqual(reverse('rest_framework:logout'), '/aether/accounts/logout/')
        self.assertEqual(reverse('rest_framework:token'), '/aether/accounts/token')
        self.assertEqual(reverse('logout'), '/aether/logout/')


@override_settings(TEST_KERNEL_ACTIVE=False)
class UrlsNoKernelTest(UrlsTestCase):

    def test__urls(self):
        self.assertRaises(exceptions.NoReverseMatch, reverse, 'check-kernel')


@override_settings(TEST_TOKEN_ACTIVE=False)
class UrlsNoTokenTest(UrlsTestCase):

    def test__urls(self):
        self.assertRaises(exceptions.NoReverseMatch, reverse, 'rest_framework:token')


@override_settings(
    CAS_SERVER_URL='http://localhost:6666',
    INSTALLED_APPS=[*settings.INSTALLED_APPS, 'django_cas_ng'],
    AUTH_URL='accounts',
)
class UrlsCASServerTest(UrlsTestCase):

    def test__urls(self):
        from django_cas_ng import views

        self.assertEqual(reverse('rest_framework:login'), '/accounts/login/')
        self.assertEqual(reverse('rest_framework:logout'), '/accounts/logout/')

        self.assertEqual(resolve('/accounts/login/').func.view_class,
                         views.LoginView.as_view().view_class)
        self.assertEqual(resolve('/accounts/logout/').func.view_class,
                         views.LogoutView.as_view().view_class)
        self.assertEqual(resolve('/logout/').func.view_class,
                         views.LogoutView.as_view().view_class)


@override_settings(
    KEYCLOAK_SERVER_URL='http://localhost:6666',
    KEYCLOAK_BEHIND_SCENES=True,
    AUTH_URL='accounts',
)
class UrlsKeycloakServerBehindTest(UrlsTestCase):

    def test__urls(self):
        from django.contrib.auth import views

        self.assertEqual(reverse('rest_framework:login'), '/accounts/login/')
        self.assertEqual(resolve('/accounts/login/').func.view_class,
                         views.LoginView.as_view().view_class)


@override_settings(
    KEYCLOAK_SERVER_URL='http://localhost:6666',
    KEYCLOAK_BEHIND_SCENES=False,
    AUTH_URL='accounts',
)
class UrlsKeycloakServerTest(UrlsTestCase):

    def test__urls(self):
        from aether.common.keycloak.views import KeycloakLoginView

        self.assertEqual(reverse('rest_framework:login'), '/accounts/login/')
        self.assertEqual(resolve('/accounts/login/').func.view_class,
                         KeycloakLoginView.as_view().view_class)


# using `docker-compose.yml` environment
class UrlsGatewayUrlTest(UrlsTestCase):

    def test__urls(self):
        self.assertEqual(reverse('health', kwargs={'realm': 'my-realm'}),
                         '/my-realm/common/health')
        self.assertEqual(resolve('/my-realm/common/health').kwargs,
                         {'realm': 'my-realm'})

        self.assertEqual(reverse('health'), '/health')
        self.assertEqual(resolve('/health').kwargs, {})

        self.assertEqual(reverse('admin:index'), '/-/common/admin/')
        self.assertEqual(reverse('rest_framework:login'), '/-/common/accounts/login/')


@override_settings(GATEWAY_SERVICE_ID=None)
class UrlsNoGatewayUrlTest(UrlsTestCase):

    def test__urls(self):
        self.assertRaises(exceptions.NoReverseMatch,
                          reverse,
                          'health',
                          kwargs={'realm': 'my-realm'})


@override_settings(ADMIN_URL='private')
class AdminUrlsUrlTest(UrlsTestCase):

    def test__urls(self):
        self.assertEqual(reverse('admin:index'), '/private/')


@override_settings(AUTH_URL='secure')
class AuthUrlsUrlTest(UrlsTestCase):

    def test__urls(self):
        self.assertEqual(reverse('rest_framework:login'), '/secure/login/')
