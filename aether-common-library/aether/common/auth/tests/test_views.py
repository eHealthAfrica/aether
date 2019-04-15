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
from importlib import import_module

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from rest_framework import status

from ..views import AetherLogoutView

user_objects = get_user_model().objects


@override_settings(MULTITENANCY=False)
class ViewsTest(TestCase):

    def setUp(self):
        self.token_url = reverse('rest_framework:token')

    def test_obtain_auth_token__as_normal_user(self):
        username = 'user'
        email = 'user@example.com'
        password = 'useruser'
        user_objects.create_user(username, email, password)
        self.assertTrue(self.client.login(username=username, password=password))

        token_username = 'username-for-token'
        self.assertEqual(user_objects.filter(username=token_username).count(), 0)

        response = self.client.post(self.token_url, data={'username': token_username})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(user_objects.filter(username=token_username).count(), 0)

    def test_obtain_auth_token__as_admin(self):
        username = 'admin'
        email = 'admin@example.com'
        password = 'adminadmin'
        user_objects.create_superuser(username, email, password)
        self.assertTrue(self.client.login(username=username, password=password))

        token_username = 'username-for-token'
        self.assertEqual(user_objects.filter(username=token_username).count(), 0)

        response = self.client.post(self.token_url, data={'username': token_username})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.json()['token']
        self.assertNotEqual(token, None)

        self.assertEqual(
            user_objects.filter(username=token_username).count(),
            1,
            'request a token for a non-existing user creates the user'
        )

        response = self.client.post(self.token_url, data={'username': token_username})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token_again = response.json()['token']
        self.assertEqual(token, token_again, 'returns the same token')

        self.assertEqual(
            user_objects.filter(username=token_username).count(),
            1,
            'request a token for an existing user does not create a new user'
        )

    def test_obtain_auth_token__raises_exception(self):
        username = 'admin'
        email = 'admin@example.com'
        password = 'adminadmin'
        user_objects.create_superuser(username, email, password)
        self.assertTrue(self.client.login(username=username, password=password))

        token_username = 'username-for-token'
        self.assertEqual(user_objects.filter(username=token_username).count(), 0)

        with mock.patch(
            'aether.common.auth.views.Token.objects.get_or_create',
            side_effect=Exception(':('),
        ):
            response = self.client.post(self.token_url, data={'username': token_username})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['message'], ':(')

    def test_logout(self):
        logout_url = reverse('logout')
        self.assertEqual(logout_url, '/logout/')
        self.assertNotEqual(logout_url, reverse('rest_framework:logout'))

        response = self.client.get(logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.template_name[0], settings.LOGGED_OUT_TEMPLATE)

        settings.SESSION_ENGINE = 'django.contrib.sessions.backends.file'
        engine = import_module(settings.SESSION_ENGINE)
        store = engine.SessionStore()
        store.save()

        request = RequestFactory().get('/')
        setattr(request, 'session', store)

        # No next page: displays logged out template
        response = AetherLogoutView.as_view(
            next_page=None,
            template_name=settings.LOGGED_OUT_TEMPLATE,
        )(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.template_name[0], settings.LOGGED_OUT_TEMPLATE)

        # No realm: goes to next page
        response = AetherLogoutView.as_view(next_page='/check-app')(request)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, '/check-app')

        # Public realm: goes to next page
        next_page = f'/{settings.GATEWAY_PUBLIC_REALM}/{settings.GATEWAY_SERVICE_ID}/check-app'
        response = AetherLogoutView.as_view(next_page=next_page)(request)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, next_page)

        # No public realm: goes to gateway logout
        next_page = f'/realm-name/{settings.GATEWAY_SERVICE_ID}/check-app'
        response = AetherLogoutView.as_view(next_page=next_page)(request)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(
            response.url,
            f'{settings.GATEWAY_HOST}/realm-name/{settings.GATEWAY_SERVICE_ID}/logout')
