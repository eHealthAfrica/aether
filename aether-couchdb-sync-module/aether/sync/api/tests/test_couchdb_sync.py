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
from unittest import mock
import requests

from django_eha_sdk.utils import get_all_docs

from ...couchdb import api as couchdb
from ..couchdb_helpers import create_db
from ..kernel_utils import (
    check_kernel_connection,
    get_kernel_auth_header,
    get_kernel_url,
)
from ..models import DeviceDB, Project, Schema

from ..couchdb_sync import (
    get_meta_doc,
    import_synced_devices,
    post_to_aether,
)
from . import ApiTestCase


KERNEL_URL = get_kernel_url()
KERNEL_HEADERS = get_kernel_auth_header()

SUBMISSION_FK = 'mappingset'
DEVICE_ID = 'test_import-from-couch'


def get_aether_submissions():
    url = f'{KERNEL_URL}/submissions/'
    return list(get_all_docs(url, headers=KERNEL_HEADERS))


class CouchDbSyncTestCase(ApiTestCase):

    def setUp(self):
        super(CouchDbSyncTestCase, self).setUp()

        # Check that we can connect to the kernel container.
        self.assertTrue(check_kernel_connection())

        # use same ID for all artefacts
        self.KERNEL_ID = str(uuid.uuid4())
        self.SCHEMA_NAME = 'example'

        Schema.objects.create(
            name=self.SCHEMA_NAME,
            kernel_id=self.KERNEL_ID,
            project=Project.objects.create(
                name=self.SCHEMA_NAME,
                project_id=self.KERNEL_ID,
            ),
            avro_schema={
                'name': 'Person',
                'type': 'record',
                'fields': [
                    {
                        'name': 'id',
                        'type': 'string',
                    },
                    {
                        'name': 'firstName',
                        'type': ['null', 'string'],
                    },
                    {
                        'name': 'familyName',
                        'type': ['null', 'string'],
                    }
                ]
            }
        )

        # An example document, which will eventually be submitted as `payload`
        # the model `aether.kernel.api.models.Submission`
        self.example_doc = {
            '_id': f'{self.SCHEMA_NAME}-aabbbdddccc',
            'deviceId': DEVICE_ID,
            'firstname': 'Han',
            'lastname': 'Solo',
        }

        self.helper__add_device_id(DEVICE_ID)

    def tearDown(self):
        super(CouchDbSyncTestCase, self).tearDown()

        requests.delete(f'{KERNEL_URL}/projects/{self.KERNEL_ID}/', headers=KERNEL_HEADERS)
        requests.delete(f'{KERNEL_URL}/schemas/{self.KERNEL_ID}/', headers=KERNEL_HEADERS)

    @mock.patch('aether.sync.api.couchdb_sync.check_kernel_connection', return_value=False)
    def test_post_to_aether_no_kernel(self, mock_test):
        self.assertRaises(
            RuntimeError,
            post_to_aether,
            document=None,
        )

    def test_post_to_aether_non_valid_arguments(self):
        self.assertRaises(
            Exception,
            post_to_aether,
            document={'_id': 'a-b'},
        )
        self.assertRaises(
            Exception,
            post_to_aether,
            document={'_id': 1},
        )

    @mock.patch('aether.sync.api.couchdb_sync.propagate_kernel_artefacts')
    @mock.patch('aether.sync.api.couchdb_sync.check_kernel_connection', return_value=True)
    @mock.patch('aether.sync.api.kernel_utils.request')
    def test_post_to_aether__without_aether_id(self, mock_req, mock_auth, mock_propagate):
        post_to_aether(document={'_id': f'{self.SCHEMA_NAME}-b'}, aether_id=None)
        mock_req.assert_called_with(
            method='post',
            url='http://kernel-test:9100/submissions/',
            json={'payload': {'_id': f'{self.SCHEMA_NAME}-b'}, 'mappingset': mock.ANY},
            headers={'Authorization': mock.ANY},
        )

    @mock.patch('aether.sync.api.couchdb_sync.propagate_kernel_artefacts')
    @mock.patch('aether.sync.api.couchdb_sync.check_kernel_connection', return_value=True)
    @mock.patch('aether.sync.api.kernel_utils.request')
    def test_post_to_aether__with_aether_id(self, mock_req, mock_auth, mock_propagate):
        post_to_aether(document={'_id': f'{self.SCHEMA_NAME}-b'}, aether_id=1)
        mock_req.assert_called_with(
            method='put',
            url='http://kernel-test:9100/submissions/1/',
            json={'payload': {'_id': f'{self.SCHEMA_NAME}-b'}, 'mappingset': mock.ANY},
            headers={'Authorization': mock.ANY},
        )

    @mock.patch('aether.sync.api.couchdb_sync.import_synced_docs',
                side_effect=Exception('mocked exception'))
    def test_import_one_document_with_error(self, mock_synced):
        # this creates a test couchdb
        device = DeviceDB(device_id=DEVICE_ID)
        device.save()
        create_db(DEVICE_ID)

        resp = couchdb.put('{}/{}'.format(device.db_name, self.example_doc['_id']),
                           json=self.example_doc)
        self.assertEqual(resp.status_code, 201, 'The example document got created')

        results = import_synced_devices()
        mock_synced.assert_called()
        self.assertNotEqual(results[0]['error'], None)
        self.assertEqual(results[0]['stats'], None)

    @mock.patch('aether.sync.api.couchdb_sync.post_to_aether',
                side_effect=Exception('mocked exception'))
    def test_import_one_document_with_with_error_in_kernel(self, mock_post):
        # this creates a test couchdb
        device = DeviceDB(device_id=DEVICE_ID)
        device.save()
        create_db(DEVICE_ID)

        resp = couchdb.put('{}/{}'.format(device.db_name, self.example_doc['_id']),
                           json=self.example_doc)
        self.assertEqual(resp.status_code, 201, 'The example document got created')

        results = import_synced_devices()
        mock_post.assert_called()
        self.assertNotEqual(results[0]['error'], None)
        self.assertEqual(results[0]['stats'], None)

    def test_import_one_document(self):
        # this creates a test couchdb
        device = DeviceDB(device_id=DEVICE_ID)
        device.save()
        create_db(DEVICE_ID)

        docs = get_aether_submissions()
        self.assertEqual(len(docs), 0, 'Nothing in Kernel yet')

        resp = couchdb.put('{}/{}'.format(device.db_name, self.example_doc['_id']),
                           json=self.example_doc)
        self.assertEqual(resp.status_code, 201, 'The example document got created')

        import_synced_devices()

        docs = get_aether_submissions()
        self.assertEqual(len(docs), 1, 'Something was created in Kernel')

        posted = docs[0]  # Aether responds with the latest post first
        self.assertEqual(
            posted[SUBMISSION_FK],
            self.KERNEL_ID,
            'Submission posted to the correct id',
        )
        for key in ['_id', 'firstname', 'lastname']:
            self.assertEqual(
                posted['payload'].get(key),
                self.example_doc.get(key),
                'posted example doc',
            )

        # check the written meta document
        status = get_meta_doc(device.db_name, self.example_doc['_id'])

        self.assertFalse('error' in status, 'no error key')
        self.assertTrue('last_rev' in status, 'last rev key')
        self.assertTrue('aether_id' in status, 'aether id key')

    def test_dont_reimport_document(self):
        # this creates a test couchdb
        device = DeviceDB(device_id=DEVICE_ID)
        device.save()
        create_db(DEVICE_ID)

        resp = couchdb.put('{}/{}'.format(device.db_name, self.example_doc['_id']),
                           json=self.example_doc)
        self.assertEqual(resp.status_code, 201, 'The example document got created')

        docs = get_aether_submissions()
        self.assertEqual(len(docs), 0, 'Nothing in Kernel yet')

        import_synced_devices()

        docs = get_aether_submissions()
        self.assertEqual(len(docs), 1, 'Something was created in Kernel')

        # reset the user to test the meta doc mechanism
        device.last_synced_seq = 0
        device.save()

        import_synced_devices()

        docs = get_aether_submissions()
        self.assertEqual(len(docs), 1, 'Document is not imported a second time')

    def test_update_document(self):
        # this creates a test couchdb
        device = DeviceDB(device_id=DEVICE_ID)
        device.save()
        create_db(DEVICE_ID)

        doc_url = '{}/{}'.format(device.db_name, self.example_doc['_id'])

        resp = couchdb.put(doc_url, json=self.example_doc)
        self.assertEqual(resp.status_code, 201, 'The example document got created')

        import_synced_devices()

        docs = get_aether_submissions()
        submission_id = docs[0]['id']

        doc_to_update = couchdb.get(doc_url).json()
        doc_to_update['firstname'] = 'Rey'
        doc_to_update['lastname'] = '(Unknown)'
        resp = couchdb.put(doc_url, json=doc_to_update)
        self.assertEqual(resp.status_code, 201, 'The example document got updated')

        import_synced_devices()

        updated = get_aether_submissions()[0]
        self.assertEqual(updated['id'], submission_id, 'updated same doc')
        self.assertEqual(
            updated['payload']['_id'],
            self.example_doc['_id'],
            'updated submission',
        )
        self.assertEqual(updated['payload']['firstname'], 'Rey', 'updated submission')
        self.assertEqual(updated['payload']['lastname'], '(Unknown)', 'updated submission')

        # check the written meta document
        status = get_meta_doc(device.db_name, self.example_doc['_id'])
        self.assertEqual(status['last_rev'][0], '2', 'updated meta document')

    def test_document_with_aether_http_error(self):
        class MockHTTPErrorResponse():
            def __init__(self):
                self.content = 'http-error'
                self.text = 'http-error'

            def raise_for_status(self):
                raise requests.exceptions.HTTPError

        # this creates a test couchdb
        device = DeviceDB(device_id=DEVICE_ID)
        device.save()
        create_db(DEVICE_ID)

        doc_url = '{}/{}'.format(device.db_name, self.example_doc['_id'])

        resp = couchdb.put(doc_url, json=self.example_doc)
        self.assertEqual(resp.status_code, 201, 'The example document got created')

        # raise error sending docs to Aether Kernel
        with mock.patch('aether.sync.api.couchdb_sync.post_to_aether',
                        return_value=MockHTTPErrorResponse()) as mock_post_to_aether:
            import_synced_devices()
            mock_post_to_aether.assert_called()

        docs = get_aether_submissions()
        self.assertEqual(len(docs), 0, 'doc did not get imported to aether')
        status = get_meta_doc(device.db_name, self.example_doc['_id'])

        self.assertIn('error', status, 'posts error key')
        self.assertNotIn('last_rev', status, 'no last rev key')
        self.assertNotIn('aether_id', status, 'no aether id key')
        self.assertIn('http-error', status['error'], 'saves error object')
