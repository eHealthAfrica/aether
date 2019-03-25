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

from . import ApiTestCase
from .. import couchdb_helpers as helpers
from ...couchdb import api


class CouchDBHelpersCredentialsTests(ApiTestCase):

    def test_generate_password(self):
        p1 = helpers.generate_password()
        self.assertEqual(len(p1), 100)
        p2 = helpers.generate_password()
        self.assertNotEqual(p1, p2)

    def test_generate_user_id(self):
        device_id = 'test_XXxx99//123?`'
        user_id = helpers.generate_user_id(device_id)
        self.assertEqual(user_id, 'org.couchdb.user:test_xxxx99123')

    def test_create_device_db_name(self):
        device_id = 'test_XXxx99//123?`'
        db_name = helpers.generate_db_name(device_id)
        self.assertEqual(db_name, 'device_test_xxxx99123')

    def test_create_device_db(self):
        device_id = self.helper__random_device_id()

        helpers.create_db(device_id)
        db_name = helpers.generate_db_name(device_id)

        db_req = api.get(db_name)
        self.assertEqual(db_req.status_code, 200, msg=db_req.text)

        sec_req = api.get(helpers.generate_db_name(device_id) + '/_security')
        self.assertEqual(sec_req.status_code, 200, sec_req.text)
        sec_doc = sec_req.json()
        self.assertIn(device_id, sec_doc['members']['roles'])

    def test_create_couchdb_user(self):
        email = 'test_user@ehealthnigeria.org'
        password = helpers.generate_password()
        device_id = self.helper__random_device_id()

        helpers.create_user(email, password, device_id)

        # Check the user exists
        user_url = '_users/' + helpers.generate_user_id(device_id)
        user_request = api.get(user_url)
        self.assertEqual(user_request.status_code, 200, msg=user_request.text)

    def test_delete_couchdb_user(self):
        email = 'test_user@ehealthnigeria.org'
        password = helpers.generate_password()
        device_id = self.helper__random_device_id()

        helpers.create_user(email, password, device_id)

        # Check the user exists
        user_url = '_users/' + helpers.generate_user_id(device_id)
        user_request = api.get(user_url)
        self.assertEqual(user_request.status_code, 200, msg=user_request.text)

        # Check the user is gone
        helpers.delete_user(device_id)
        user_request = api.get(user_url)
        self.assertEqual(user_request.status_code, 404, msg=user_request.text)

    def test_update_user_password(self):
        email = 'test_user2@ehealthnigeria.org'
        password = helpers.generate_password()
        device_id = self.helper__random_device_id()

        helpers.create_user(email, password, device_id)

        new_password = 'super secure new password'

        user_url = '_users/' + helpers.generate_user_id(device_id)
        user_doc = api.get(user_url).json()
        key = user_doc['derived_key']

        helpers.update_user(user_url, new_password, device_id, user_doc)

        user_doc = api.get(user_url).json()
        self.assertNotEqual(user_doc['derived_key'], key)

    def test_create_or_update(self):
        email = 'test_user3@ehealthnigeria.org'
        device_id = self.helper__random_device_id()

        helpers.create_or_update_user(email, device_id)

        user_url = '_users/' + helpers.generate_user_id(device_id)
        user_req = api.get(user_url)
        self.assertEqual(user_req.status_code, 200, msg=user_req.text)

        user_doc = user_req.json()
        rev = user_doc['_rev']
        key = user_doc['derived_key']

        helpers.create_or_update_user(email, device_id)

        user_req = api.get(user_url)
        self.assertEqual(user_req.status_code, 200, msg=user_req.text)

        user_doc = user_req.json()
        self.assertNotEqual(rev, user_doc['_rev'])
        self.assertNotEqual(key, user_doc['derived_key'])
