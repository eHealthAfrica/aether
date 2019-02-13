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
from django.test import TestCase

from .. import couchdb_helpers


class MockResponse:
    def __init__(self, status_code, json_data=None):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


class CouchdbHelpersTests(TestCase):

    def test_filter_id(self):
        self.assertRaises(Exception, couchdb_helpers.filter_id, device_id=None)
        self.assertEqual(couchdb_helpers.filter_id(''), '')
        self.assertEqual(couchdb_helpers.filter_id('a.b,c;d;e:f+g<h>i'), 'abcdefghi')

    def test_generate_password(self):
        self.assertEqual(len(couchdb_helpers.generate_password()), 100)

    def test_generate_user_id(self):
        self.assertEqual(
            couchdb_helpers.generate_user_id('a.b,c;d;e:f+g<h>i'),
            'org.couchdb.user:abcdefghi')

    def test_generate_db_name(self):
        self.assertEqual(
            couchdb_helpers.generate_db_name('a.b,c;d;e:f+g<h>i'),
            'device_abcdefghi')

    def test_create_db_none(self):
        self.assertRaises(Exception, couchdb_helpers.create_db, device_id=None)

    @mock.patch('aether.sync.api.couchdb_helpers.setup.setup_db', side_effect=Exception)
    def test_create_db_error(self, setup_db_function):
        self.assertRaises(Exception, couchdb_helpers.create_db, device_id='test_xxx')
        setup_db_function.assert_called_with('device_test_xxx', mock.ANY)

    @mock.patch('aether.sync.api.couchdb_helpers.setup.setup_db')
    def test_create_db(self, setup_db_function):
        couchdb_helpers.create_db(device_id='test_xxx')
        setup_db_function.assert_called_with('device_test_xxx', mock.ANY)

    def test_create_user_password(self):
        self.assertRaises(Exception,
                          couchdb_helpers.create_user,
                          email='',
                          password=None,
                          device_id='',
                          )

    @mock.patch('aether.sync.api.couchdb_helpers.api.put')
    def test_create_user(self, put_function):
        couchdb_helpers.create_user(
            email='test@test.com',
            password='secret',
            device_id='test_xxx',
        )
        put_function.assert_called_with(
            '_users/org.couchdb.user:test_xxx',
            json={
                'name': 'test_xxx',
                'password': 'secret',
                'roles': ['test_xxx'],
                'type': 'user',
                'email': 'test@test.com',
                'mobile_user': True
            })

    @mock.patch('aether.sync.api.couchdb_helpers.api')
    def test_update_user(self, api_mock):
        couchdb_helpers.update_user(
            url='https://test',
            password='secret',
            device_id='test_xxx',
            existing={
                'derived_key': 'any',
                'salt': 'any',
                'password': 'any',
                'roles': ['test_zzz']
            })

        api_mock.put.assert_called_with(
            'https://test',
            json={
                'password': 'secret',
                'roles': ['test_zzz', 'test_xxx']
            })

    @mock.patch('aether.sync.api.couchdb_helpers.api')
    def test_create_or_update_user(self, api_mock):
        self.assertRaises(
            ValueError,
            couchdb_helpers.create_or_update_user,
            email=None,
            device_id=None)
        self.assertRaises(
            ValueError,
            couchdb_helpers.create_or_update_user,
            email='test@test.com',
            device_id=None)
        self.assertRaises(
            ValueError,
            couchdb_helpers.create_or_update_user,
            email='test@test.com',
            device_id=';;;;')
        self.assertRaises(
            ValueError,
            couchdb_helpers.create_or_update_user,
            email='test@test.com',
            device_id='admin')

        # new user
        api_mock.get.return_value = MockResponse(status_code=404)
        couchdb_helpers.create_or_update_user(email='test@test.com', device_id='test_xxx')
        api_mock.get.assert_called_with('_users/org.couchdb.user:test_xxx')
        api_mock.put.assert_called_with('_users/org.couchdb.user:test_xxx', json=mock.ANY)

        # update user
        existing = {
            'derived_key': 'any',
            'salt': 'any',
            'password': 'secret',
            'roles': ['test_zzz']
        }
        api_mock.get.return_value = MockResponse(status_code=200, json_data=existing)
        updated = couchdb_helpers.create_or_update_user(email='test@test.com', device_id='test_xxx')
        api_mock.get.assert_called_with('_users/org.couchdb.user:test_xxx')
        api_mock.put.assert_called_with('_users/org.couchdb.user:test_xxx', json=mock.ANY)
        self.assertNotEqual(updated['password'], 'secret')

    @mock.patch('aether.sync.api.couchdb_helpers.api')
    def test_delete_user(self, api_mock):
        self.assertRaises(Exception, couchdb_helpers.delete_user, device_id=None)

        api_mock.get.return_value = MockResponse(status_code=404)
        couchdb_helpers.delete_user(device_id='test_xxx')
        api_mock.get.assert_called_with('_users/org.couchdb.user:test_xxx')
        api_mock.delete.assert_not_called()

        api_mock.get.return_value = MockResponse(status_code=200, json_data={'_rev': 1})
        couchdb_helpers.delete_user(device_id='test_xxx')
        api_mock.get.assert_called_with('_users/org.couchdb.user:test_xxx')
        api_mock.delete.assert_called_with('_users/org.couchdb.user:test_xxx?rev=1')

    @mock.patch('aether.sync.api.couchdb_helpers.api.post')
    def test_create_document(self, post_function):
        couchdb_helpers.create_document(device_id='abc123', doc={'_id': 'test'})
        post_function.assert_called_with('device_abc123', json={'_id': 'test'})
