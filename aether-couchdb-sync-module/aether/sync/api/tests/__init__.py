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

import re
from django.test import TransactionTestCase

from ...couchdb import api

db_name_test = re.compile('^device_test_')


def clean_couch():
    '''
    Cleans up all the CouchDB users starting with test_
    and all the databases starting with device_test
    '''
    testusers = api \
        .get('_users/_all_docs?' +
             'startkey="org.couchdb.user:test_"' +
             '&endkey="org.couchdb.user:test_%7B%7D"') \
        .json()
    for user in testusers['rows']:
        api.delete('_users/{}?rev={}'.format(user['id'], user['value']['rev']))

    # deleteing all the test dbs
    testdbs = filter(db_name_test.match, api.get('_all_dbs').json())
    for db in testdbs:
        api.delete(db)


class ApiTestCase(TransactionTestCase):

    def tearDown(self):
        clean_couch()
