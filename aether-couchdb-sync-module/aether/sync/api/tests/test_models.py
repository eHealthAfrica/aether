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

import uuid
from django.db import IntegrityError

from ...couchdb import api
from . import ApiTestCase
from .. import couchdb_helpers
from ..models import MobileUser, DeviceDB, Project, Schema


class ModelsTests(ApiTestCase):

    def test_mobileuser_str(self):
        email = 'test_ally@ehealthnigeria.org'
        test_user = MobileUser.objects.create(email=email)

        self.assertTrue(email in str(test_user))

    def test_create_user_model(self):
        '''
        Test that we create the MobileUsers with email as unique primary key,
        and that we can find them
        '''
        email = 'test_karl@ehealthnigeria.org'
        first_user = MobileUser.objects.create(email=email)
        self.assertEqual(str(first_user), email)

        self.assertRaises(
            IntegrityError,
            MobileUser.objects.create,
            email=email)

        found_user = MobileUser.objects.get(email=email)

        self.assertEquals(first_user, found_user, 'retrieves user via email')

    def test_delete_user_model(self):
        '''
        Tests that the MobileUser model and the CouchDB users work together,
        that CouchDB users that have been created for a MobileUser gets deleted,
        but that the database is kept (so we don't delete data)
        '''
        email = 'test_till@ehealthnigeria.org'
        device_id = 'device_x'
        test_user = MobileUser.objects.create(email=email)
        test_device = DeviceDB(device_id=device_id, mobileuser=test_user)

        couchdb_helpers.create_or_update_user(email, device_id)

        test_user.save()
        test_device.save()

        user_req = api.get('_users/' + couchdb_helpers.generate_user_id(device_id))
        self.assertEqual(user_req.status_code, 200, user_req.text)
        self.assertIn(device_id, user_req.json()['roles'])

        test_user.delete()

        couch_user2 = api.get('_users/' + couchdb_helpers.generate_user_id(device_id))
        self.assertEqual(couch_user2.status_code, 404, msg='couchdb user has been deleted')

    def test_delete_user_model_no_couch_user(self):
        '''
        Test that the model doesn't throw errors on non-existing couch user
        '''
        email = 'test_ally@ehealthnigeria.org'
        test_user = MobileUser.objects.create(email=email)

        test_user.email = 'does@not.exist'
        # test_user.couchdb_id = 'org.couchdb.user:{}'.format(email)
        test_user.save()
        test_user.delete()
        self.assertTrue(True, 'Non-existing couch user did not throw an error')

    def test_create_devicedb_model(self):
        device_id = 'test_Xx'
        devicedb = DeviceDB(device_id=device_id)
        devicedb.save()
        self.assertEqual(str(devicedb), device_id)
        couchdb_helpers.create_db(device_id)

        db_req = api.get(couchdb_helpers.generate_db_name(device_id))
        self.assertEqual(db_req.status_code, 200, db_req.text)

        with self.assertRaises(IntegrityError):
            DeviceDB(device_id=device_id).save()

        found_db = DeviceDB.objects.get(device_id=device_id)

        self.assertEquals(devicedb, found_db, 'retrieves db via device-id')

    def test_devicedb_and_user_roles(self):
        device_id = 'test_Xx'
        device_id2 = 'test_Xx_2'
        db_name = couchdb_helpers.generate_db_name(device_id)
        db_name2 = couchdb_helpers.generate_db_name(device_id2)

        user = MobileUser(email='test_karl@ehealthnigeria.org')
        user.save()

        creds = couchdb_helpers.create_or_update_user(user.email, device_id)
        user_auth = (creds['username'], creds['password'])

        user_req = api.get('_users/' + couchdb_helpers.generate_user_id(device_id))
        self.assertEqual(user_req.status_code, 200, user_req.text)
        user_doc = user_req.json()
        self.assertIn(device_id, user_doc['roles'])
        self.assertNotIn(device_id2, user_doc['roles'])

        device_db = DeviceDB(device_id=device_id)
        device_db.save()
        couchdb_helpers.create_db(device_id)

        db_req = api.get(db_name)
        self.assertEqual(db_req.status_code, 200, db_req.text)

        device_db2 = DeviceDB(device_id=device_id2)
        device_db2.save()
        couchdb_helpers.create_db(device_id2)

        db_req2 = api.get(db_name2)
        self.assertEqual(db_req2.status_code, 200, db_req.text)

        # User has access to db1 because it's in his role
        user_db_req = api.get(db_name, auth=user_auth)
        self.assertEqual(user_db_req.status_code, 200, user_db_req.text)

        # User has no access to db2
        user_db_req2 = api.get(db_name2, auth=user_auth)
        self.assertEqual(user_db_req2.status_code, 403, user_db_req2.text)

        # Grant user access to db2
        creds = couchdb_helpers.create_or_update_user(user.email, device_id2)
        user_auth = (creds['username'], creds['password'])

        # User now has access to db2
        user_db_req2 = api.get(db_name2, auth=user_auth)
        self.assertEqual(user_db_req2.status_code, 200, user_db_req2.text)

    def test_devicedb_dbname(self):
        device_id = 'test_XxYyZz987654321'
        db_name = couchdb_helpers.generate_db_name(device_id)
        devicedb = DeviceDB(device_id=device_id)

        self.assertEqual(devicedb.db_name, db_name)

    def test_project_and_schema_create(self):
        name = 'village'
        id = uuid.uuid4()

        project = Project.objects.create(name=name, project_id=id)
        self.assertEqual(str(project), f'{id} - {name}')

        schema = Schema.objects.create(name=name, project=project)
        self.assertEqual(str(schema), name)

        schema_2 = Schema.objects.create(
            project=project,
            avro_schema={'name': 'name'}
        )
        self.assertEqual(str(schema_2), 'name')
