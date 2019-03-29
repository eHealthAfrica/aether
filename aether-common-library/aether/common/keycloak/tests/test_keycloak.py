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

from http.cookies import SimpleCookie
from importlib import import_module

from django.conf import settings
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from ...tests import MockResponse
from ..utils import _KC_TOKEN_SESSION as TOKEN_KEY

user_objects = get_user_model().objects


class KeycloakTests(TestCase):

    def test__workflow(self):

        FAKE_TOKEN = {
            'access_token': 'access-keycloak',
            'refresh_token': 'refresh-keycloak',
        }
        REALM = 'testing'

        # login using accounts login entrypoint
        LOGIN_URL = reverse('rest_framework:login')
        SAMPLE_URL = reverse('testmodel-list')

        settings.SESSION_ENGINE = 'django.contrib.sessions.backends.file'
        engine = import_module(settings.SESSION_ENGINE)
        store = engine.SessionStore()
        store.save()

        self.client.cookies = SimpleCookie({settings.SESSION_COOKIE_NAME: store.session_key})
        self.assertIsNotNone(self.client.session)

        # visit any page that requires authentication (without being logged)
        response = self.client.get(SAMPLE_URL)
        self.assertEqual(response.status_code, 403)

        # make realm check fail
        with mock.patch('aether.common.keycloak.utils.exec_request',
                        side_effect=[
                            # check realm request
                            MockResponse(status_code=404),
                        ]) as mock_req_1:
            response = self.client.post(LOGIN_URL, data={
                'username': 'user',
                'password': 'secretsecret',
                'realm': 'fake',
            })
            content = response.content.decode('utf-8')
            self.assertIn('Please correct the error below.', content)
            self.assertIn('Invalid realm', content)

            session = self.client.session
            self.assertIsNone(session.get(TOKEN_KEY))
            self.assertIsNone(session.get(settings.REALM_COOKIE))

            mock_req_1.assert_called_once_with(
                method='head',
                url=f'{settings.KEYCLOAK_SERVER_URL}/fake/account',
            )

        # make get `token` from keyclock fail
        with mock.patch('aether.common.keycloak.utils.exec_request',
                        side_effect=[
                            # check realm request
                            MockResponse(status_code=204),
                            # get token from keycloak
                            MockResponse(status_code=400),
                        ]) as mock_req_2:
            response = self.client.post(LOGIN_URL, data={
                'username': 'user',
                'password': 'secretsecret',
                'realm': REALM,
            })
            content = response.content.decode('utf-8')
            self.assertIn('Please enter a correct username and password.', content)
            self.assertIn('Note that both fields may be case-sensitive.', content)

            mock_req_2.assert_has_calls([
                mock.call(
                    method='head',
                    url=f'{settings.KEYCLOAK_SERVER_URL}/{REALM}/account',
                ),
                mock.call(
                    method='post',
                    url=f'{settings.KEYCLOAK_SERVER_URL}/{REALM}/protocol/openid-connect/token',
                    data={
                        'grant_type': 'password',
                        'client_id': settings.KEYCLOAK_CLIENT_ID,
                        'username': 'user',
                        'password': 'secretsecret',
                    },
                ),
            ])

        # make get `userinfo` from keyclock fail (unlikely if `token` doesn't)
        with mock.patch('aether.common.keycloak.utils.exec_request',
                        side_effect=[
                            # check realm request
                            MockResponse(status_code=204),
                            # get token from keycloak
                            MockResponse(status_code=200, json_data=FAKE_TOKEN),
                            # get userinfo from keycloak
                            MockResponse(status_code=404),
                        ]) as mock_req_3:
            response = self.client.post(LOGIN_URL, data={
                'username': 'user',
                'password': 'secretsecret',
                'realm': REALM,
            })
            content = response.content.decode('utf-8')
            self.assertIn('Please enter a correct username and password.', content)
            self.assertIn('Note that both fields may be case-sensitive.', content)

            mock_req_3.assert_has_calls([
                mock.call(
                    method='head',
                    url=f'{settings.KEYCLOAK_SERVER_URL}/{REALM}/account',
                ),
                mock.call(
                    method='post',
                    url=f'{settings.KEYCLOAK_SERVER_URL}/{REALM}/protocol/openid-connect/token',
                    data={
                        'grant_type': 'password',
                        'client_id': settings.KEYCLOAK_CLIENT_ID,
                        'username': 'user',
                        'password': 'secretsecret',
                    },
                ),
                mock.call(
                    method='get',
                    url=f'{settings.KEYCLOAK_SERVER_URL}/{REALM}/protocol/openid-connect/userinfo',
                    headers={'Authorization': 'Bearer {}'.format(FAKE_TOKEN['access_token'])},
                ),
            ])

        # finally, logs in
        with mock.patch('aether.common.keycloak.utils.exec_request',
                        side_effect=[
                            # check realm request
                            MockResponse(status_code=204),
                            # get token from keycloak
                            MockResponse(status_code=200, json_data=FAKE_TOKEN),
                            # get userinfo from keycloak
                            MockResponse(status_code=200, json_data={
                                'given_name': 'given',
                                'family_name': 'family',
                                'email': 'user@example.com',
                            }),
                        ]) as mock_req_4:
            self.assertEqual(user_objects.filter(username='testing__user').count(), 0)
            response = self.client.post(LOGIN_URL, data={
                'username': 'user',
                'password': 'secretsecret',
                'realm': REALM,
            })
            self.assertEqual(user_objects.filter(username='testing__user').count(), 1)
            user = user_objects.get(username='testing__user')
            self.assertEqual(user.first_name, 'given')
            self.assertEqual(user.last_name, 'family')
            self.assertEqual(user.email, 'user@example.com')

            session = self.client.session
            self.assertEqual(session.get(TOKEN_KEY), FAKE_TOKEN)
            self.assertEqual(session.get(settings.REALM_COOKIE), REALM)

            mock_req_4.assert_has_calls([
                mock.call(
                    method='head',
                    url=f'{settings.KEYCLOAK_SERVER_URL}/{REALM}/account',
                ),
                mock.call(
                    method='post',
                    url=f'{settings.KEYCLOAK_SERVER_URL}/{REALM}/protocol/openid-connect/token',
                    data={
                        'grant_type': 'password',
                        'client_id': settings.KEYCLOAK_CLIENT_ID,
                        'username': 'user',
                        'password': 'secretsecret',
                    },
                ),
                mock.call(
                    method='get',
                    url=f'{settings.KEYCLOAK_SERVER_URL}/{REALM}/protocol/openid-connect/userinfo',
                    headers={'Authorization': 'Bearer {}'.format(FAKE_TOKEN['access_token'])},
                ),
            ])

        # visit any page that requires authentication
        with mock.patch('aether.common.keycloak.utils.exec_request',
                        side_effect=[
                            # refresh token in keycloak
                            MockResponse(status_code=200, json_data=FAKE_TOKEN),
                        ]) as mock_req_5:

            response = self.client.get(SAMPLE_URL)
            self.assertEqual(response.status_code, 200)

            mock_req_5.assert_called_once_with(
                method='post',
                url=f'{settings.KEYCLOAK_SERVER_URL}/{REALM}/protocol/openid-connect/token',
                data={
                    'grant_type': 'refresh_token',
                    'client_id': settings.KEYCLOAK_CLIENT_ID,
                    'refresh_token': FAKE_TOKEN['refresh_token'],
                },
            )

        # visit any page that requires authentication and fails
        with mock.patch('aether.common.keycloak.utils.exec_request',
                        side_effect=[
                            # refresh token in keycloak
                            MockResponse(status_code=400),
                            # log outs call
                            MockResponse(status_code=204),
                        ]) as mock_req_6:

            response = self.client.get(SAMPLE_URL)
            self.assertEqual(response.status_code, 403)

            mock_req_6.assert_has_calls([
                mock.call(
                    method='post',
                    url=f'{settings.KEYCLOAK_SERVER_URL}/{REALM}/protocol/openid-connect/token',
                    data={
                        'grant_type': 'refresh_token',
                        'client_id': settings.KEYCLOAK_CLIENT_ID,
                        'refresh_token': FAKE_TOKEN['refresh_token'],
                    },
                ),
                mock.call(
                    method='post',
                    url=f'{settings.KEYCLOAK_SERVER_URL}/{REALM}/protocol/openid-connect/logout',
                    data={
                        'client_id': settings.KEYCLOAK_CLIENT_ID,
                        'refresh_token': FAKE_TOKEN['refresh_token'],
                    },
                ),
            ])

        # side effect of being logged out
        session = self.client.session
        self.assertIsNone(session.get(TOKEN_KEY))
        self.assertIsNone(session.get(settings.REALM_COOKIE))

        # logs in again
        with mock.patch('aether.common.keycloak.utils.exec_request',
                        side_effect=[
                            # check realm request
                            MockResponse(status_code=204),
                            # get token from keycloak
                            MockResponse(status_code=200, json_data=FAKE_TOKEN),
                            # get userinfo from keycloak
                            MockResponse(status_code=200, json_data={
                                'given_name': 'John',
                                'family_name': 'Doe',
                                'email': 'john.doe@example.com',
                            }),
                        ]):
            response = self.client.post(LOGIN_URL, data={
                'username': 'user',
                'password': 'secretsecret',
                'realm': REALM,
            })
            # user data is updated
            user = user_objects.get(username='testing__user')
            self.assertEqual(user.first_name, 'John')
            self.assertEqual(user.last_name, 'Doe')
            self.assertEqual(user.email, 'john.doe@example.com')

        # logs out
        with mock.patch('aether.common.keycloak.utils.exec_request') as mock_req_7:
            self.client.logout()

            mock_req_7.assert_called_once_with(
                method='post',
                url=f'{settings.KEYCLOAK_SERVER_URL}/{REALM}/protocol/openid-connect/logout',
                data={
                    'client_id': settings.KEYCLOAK_CLIENT_ID,
                    'refresh_token': FAKE_TOKEN['refresh_token'],
                },
            )

        session = self.client.session
        self.assertIsNone(session.get(TOKEN_KEY))
        self.assertIsNone(session.get(settings.REALM_COOKIE))

        # logs out and visit any page again
        with mock.patch('aether.common.keycloak.utils.exec_request') as mock_req_8:
            self.client.logout()
            self.assertEqual(self.client.get(SAMPLE_URL).status_code, 403)

            mock_req_8.assert_not_called()
