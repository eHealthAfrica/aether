# Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
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

from django.test import override_settings
from django.urls import reverse
from oauth2client.client import VerifyJwtTokenError
from oauth2client.crypt import AppIdentityError

# This was really helpful about mocking:
# http://fgimian.github.io/blog/2014/04/10/using-the-python-mock-library-to-fake-regular-functions-during-tests/
from unittest import mock

from ...couchdb import api
from ..models import MobileUser, DeviceDB
from . import ApiTestCase


# Mocks for different scenarios
# of what could play out in the verify_token_id function
def valid_token(token, client_id):
    assert token, 'need a token passed'
    assert client_id, 'need a client id passed'

    return {
        'hd': 'ehealthnigeria.org',
        'family_name': 'Device11',
        'azp': client_id,
        'email': 'test_karl@ehealthnigeria.org',
        'iss': 'https://accounts.google.com',
        'locale': 'en',
        'sub': '100377948646174944684',
        'iat': 1475594698,
        'email_verified': True,
        'name': 'Aether Device11',
        'aud': client_id,
        'picture': 'picture.png',
        'given_name': 'AE',
        'exp': 1475598298,
    }


def just_return(token, client_id):
    return {'email': 'test_karl@ehealthnigeria.org'}


def identity_error(token, client_id):
    if token == 'invalid':
        raise AppIdentityError('Token Not Valid')

    return {'email': 'test_karl@ehealthnigeria.org'}


def wrong_email(token, client_id):
    return {'email': 'test_unknown@ehealthnigeria.org'}


def no_email(token, client_id):
    return {'email': ''}


def http_error(token, client_id):
    raise VerifyJwtTokenError('Could not get google certs for verification')


@override_settings(GOOGLE_CLIENT_ID='test-client-id')
class SigninViewTests(ApiTestCase):
    fixtures = ['mobile_users.json']
    url = reverse('signin')

    def test_register_url(self):
        self.assertTrue(self.url, msg='The sync url is defined')

    def test_setup_fixtures(self):
        self.assertEqual(MobileUser.objects.count(), 2, msg='fixtures have been added')
        self.assertTrue(
            MobileUser.objects.get(email='test_karl@ehealthnigeria.org'),
            msg='finds my testuser')

    @mock.patch('oauth2client.client.verify_id_token', side_effect=valid_token)
    def test_get_credentials(self, verify_token_function):
        '''happy path test, the user is in the MobileUsers pool '''

        device_id = self.helper__random_device_id()
        response = self.client.post(self.url, {'idToken': 'Long JWT Token', 'deviceId': device_id})
        self.assertEqual(response.status_code, 201)
        creds = response.data

        self.assertEqual(creds['username'], device_id)
        self.assertTrue(creds['password'], msg='provides a password')
        self.assertTrue(creds['url'], msg='provides a url to the couchdb')

        # Check that a device db now exists. This would raise otherwise
        device_db = DeviceDB.objects.get(device_id=device_id)
        self.assertIsNotNone(device_db, 'The device db should exist')

    @mock.patch('oauth2client.client.verify_id_token', side_effect=valid_token)
    def test_update_credentials(self, verify_token_function):
        '''happy path test, the user is in the MobileUsers pool '''

        device_id = self.helper__random_device_id()
        response = self.client.post(self.url, {'idToken': 'Long JWT Token', 'deviceId': device_id})
        self.assertEqual(response.status_code, 201)
        creds = response.data

        response2 = self.client.post(self.url, {'idToken': 'Long JWT Token', 'deviceId': device_id})
        self.assertEqual(response2.status_code, 201)
        creds2 = response2.data

        self.assertEqual(creds['username'], creds2['username'])
        self.assertEqual(creds['url'], creds2['url'])
        self.assertTrue(creds2['password'], msg='provides a new password')
        self.assertNotEqual(creds['password'], creds2['password'], msg='creates a new password')

    @mock.patch('oauth2client.client.verify_id_token', side_effect=valid_token)
    def test_two_users_one_email(self, verify_token_function):
        '''should be able to create multiple users on one email address'''

        device_id = self.helper__random_device_id()
        response = self.client.post(self.url, {'idToken': 'Long JWT Token', 'deviceId': device_id})
        self.assertEqual(response.status_code, 201)
        creds = response.data

        device_id2 = self.helper__random_device_id()
        response2 = self.client.post(self.url, {'idToken': 'Long JWT Token', 'deviceId': device_id2})
        self.assertEqual(response2.status_code, 201)
        creds2 = response2.data

        self.assertNotEqual(creds['username'], creds2['username'])
        self.assertNotEqual(creds['url'], creds2['url'])

        test_creds1 = api.get(creds['db'], auth=(creds['username'], creds['password']))
        self.assertEqual(test_creds1.status_code, 200, test_creds1.text)

        test_creds2 = api.get(creds2['db'], auth=(creds2['username'], creds2['password']))
        self.assertEqual(test_creds2.status_code, 200, test_creds2.text)

        test_creds1vs2 = api.get(creds2['db'], auth=(creds['username'], creds['password']))
        self.assertEqual(test_creds1vs2.status_code, 403, test_creds1vs2.text)

    @mock.patch('oauth2client.client.verify_id_token', side_effect=just_return)
    def test_no_token(self, valid_token_function):
        '''what happens if no token is posted?'''

        device_id = self.helper__random_device_id()
        response = self.client.post(self.url, {'idToken': '', 'deviceId': device_id})
        self.assertEqual(response.status_code, 400, 'returns error when no token is passed')

    @mock.patch('oauth2client.client.verify_id_token', side_effect=valid_token)
    def test_no_device_id(self, valid_token_function):
        '''what happens if no device id is posted?'''
        response = self.client.post(self.url, {'idToken': 'Long JWT Token', 'deviceId': ''})
        self.assertEqual(response.status_code, 400, 'returns error when no device_id is passed')

    @mock.patch('oauth2client.client.verify_id_token', side_effect=identity_error)
    def test_invalid_token(self, valid_token_function):
        '''what happens if token can not be verified?'''

        device_id = self.helper__random_device_id()
        response = self.client.post(self.url, {'idToken': 'invalid', 'deviceId': device_id})
        self.assertEqual(response.status_code, 401, 'returns error when no token is passed')

    @mock.patch('oauth2client.client.verify_id_token', side_effect=wrong_email)
    def test_valid_token_no_access(self, valid_token_function):
        '''a token with an email not in the MobileUsers list'''

        device_id = self.helper__random_device_id()
        response = self.client.post(self.url, {'idToken': 'Long JWT Token', 'deviceId': device_id})
        self.assertEqual(
            response.status_code, 403,
            'returns forbidden when email is not recognized')

    @mock.patch('oauth2client.client.verify_id_token', side_effect=no_email)
    def test_weird_token_no_email(self, valid_token_function):
        '''somehow, the token has no email address'''

        device_id = self.helper__random_device_id()
        response = self.client.post(self.url, {'idToken': 'Long JWT Token', 'deviceId': device_id})
        self.assertEqual(response.status_code, 500, 'returns server error on no email')

    @override_settings(GOOGLE_CLIENT_ID='')
    @mock.patch('oauth2client.client.verify_id_token', side_effect=just_return)
    def test_no_client_id(self, valid_token_function):
        '''forgot to set GOOGLE_CLIENT_ID, this would open up for any google JW Token'''

        device_id = self.helper__random_device_id()
        response = self.client.post(self.url, {'idToken': 'Long JWT Token', 'deviceId': device_id})
        self.assertEqual(response.status_code, 500, 'returns server error on no email')

    @mock.patch('oauth2client.client.verify_id_token', side_effect=http_error)
    def test_no_google_certs(self, valid_token_function):
        device_id = self.helper__random_device_id()
        response = self.client.post(self.url, {'idToken': 'Long JWT Token', 'deviceId': device_id})
        self.assertEqual(response.status_code, 500, 'returns server error')

    @mock.patch('aether.sync.api.views.create_or_update_user', side_effect=ValueError)
    @mock.patch('oauth2client.client.verify_id_token', side_effect=valid_token)
    def test_create_or_update_user_error(self,
                                         valid_token_function,
                                         create_or_update_user_function):
        '''somehow, the couchdb database does not respond'''

        device_id = self.helper__random_device_id()
        response = self.client.post(self.url, {'idToken': 'Long JWT Token', 'deviceId': device_id})
        self.assertEqual(response.status_code, 500, 'returns server error')
        create_or_update_user_function.assert_called_with('test_karl@ehealthnigeria.org', device_id)

    @mock.patch('aether.sync.api.views.create_db', side_effect=ValueError)
    @mock.patch('oauth2client.client.verify_id_token', side_effect=valid_token)
    def test_create_db_error(self, valid_token_function, create_db_function):
        '''somehow, the couchdb database does not respond'''

        device_id = self.helper__random_device_id()
        response = self.client.post(self.url, {'idToken': 'Long JWT Token', 'deviceId': device_id})
        self.assertEqual(response.status_code, 500, 'returns server error')
        create_db_function.assert_called_with(device_id)
