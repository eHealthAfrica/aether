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

from aether.sync.api.tests import ApiTestCase, DEVICE_TEST_FILE

from ..couchdb_file import load_backup_file


class LoadFileViewsTests(ApiTestCase):

    def test__load_backup_file(self):
        with open(DEVICE_TEST_FILE, 'rb') as fp:
            stats = load_backup_file(fp)

        self.assertEqual(
            stats,
            {
                'total': 3,
                'success': 2,
                'erred': 1,
                'err_docs': [
                    {'deviceId': 'test_abc123', '_id': 'sample-3', '_rev': 'rev-1'},
                ],
                'errors': {
                    'sample-3': {'error': 'bad_request', 'reason': 'Invalid rev format'},
                }
            }
        )

    @mock.patch('aether.sync.api.couchdb_file.create_db', side_effect=Exception)
    def test__load_backup_file__couchdb_error(self, mock_create_db):
        with open(DEVICE_TEST_FILE, 'rb') as fp:
            stats = load_backup_file(fp)

        self.assertEqual(
            stats,
            {
                'total': 3,
                'success': 0,
                'erred': 3,
                'err_docs': [
                    {'deviceId': 'test_abc123', '_id': 'sample-1'},
                    {'deviceId': 'test_abc123', '_id': 'sample-2'},
                    {'deviceId': 'test_abc123', '_id': 'sample-3', '_rev': 'rev-1'},
                ],
                'errors': {
                    'sample-1': {'error': 'not_found', 'reason': 'no_db_file'},
                    'sample-2': {'error': 'not_found', 'reason': 'no_db_file'},
                    'sample-3': {'error': 'not_found', 'reason': 'no_db_file'},
                }
            }
        )
        mock_create_db.assert_called()
