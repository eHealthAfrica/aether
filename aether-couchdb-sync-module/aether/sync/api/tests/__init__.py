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

import random
import re
import string

from django.test import TransactionTestCase

from ...couchdb import api
from .. import couchdb_helpers

ALPHANUM = string.ascii_lowercase + string.digits
DB_NAME_TEST_RE = re.compile(r'^device_test_')
DEVICE_TEST_FILE = '/code/aether/sync/api/tests/files/device_sync.json'


class ApiTestCase(TransactionTestCase):

    def setUp(self):
        super(ApiTestCase, self).setUp()

        self.TEST_DEVICES = set()
        self.TEST_USERS = set()

    def tearDown(self):
        '''
        Cleans up all the CouchDB users starting with "test_"
        and all the databases starting with "device_test_"
        '''

        testusers = api \
            .get('_users/_all_docs?startkey="org.couchdb.user:test_"&endkey="org.couchdb.user:test_%7B%7D"') \
            .json()
        for user in testusers['rows']:
            if user['id'] in self.TEST_USERS:
                api.delete('_users/{}?rev={}'.format(user['id'], user['value']['rev']))

        # deleting all the test dbs
        testdbs = filter(DB_NAME_TEST_RE.match, api.get('_all_dbs').json())
        for db in testdbs:
            if db in self.TEST_DEVICES:
                api.delete(db)

        super(ApiTestCase, self).tearDown()

    def helper__add_device_id(self, device_id):
        # add the id to the users and devices list
        self.TEST_DEVICES.add(couchdb_helpers.generate_db_name(device_id))
        self.TEST_USERS.add(couchdb_helpers.generate_user_id(device_id))

    def helper__random_device_id(self):
        # Tests are run in parallel so we try to avoid annoying errors with duplicated devices.
        device_id = 'test_' + ''.join([random.choice(ALPHANUM) for x in range(10)])
        self.helper__add_device_id(device_id)
        return device_id
