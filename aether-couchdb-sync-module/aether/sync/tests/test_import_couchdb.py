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
# software distributed under the License is distributed on anx
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import mock
import requests
from django.test import TestCase

from aether.common.kernel import utils as kernel_utils

from ..api.couchdb_helpers import create_db, generate_password as random_string
from ..api.models import DeviceDB
from ..api.tests import clean_couch
from ..couchdb import api as couchdb
from ..import_couchdb import (
    get_meta_doc,
    get_surveys_mapping,
    import_synced_devices,
    post_to_aether,
)


def get_aether_mappings():
    url = kernel_utils.get_mappings_url()
    return kernel_utils.get_all_docs(url)


def get_aether_submissions(mapping_id):
    url = kernel_utils.get_submissions_url()
    return kernel_utils.get_all_docs(url)


headers_testing = kernel_utils.get_auth_header()
device_id = 'test_import-from-couch'


class ImportTestCase(TestCase):

    def setUp(self):
        '''
        Set up a basic Aether project. This assumes that the fixture in
        `/aether-kernel/aether/kernel/api/tests/fixtures/project.json` has been
        loaded into the kernel database. See `/scripts/test_all.sh` for details.
        '''
        clean_couch()
        # Check that we can connect to the kernel container.
        self.assertTrue(kernel_utils.test_connection())
        # Delete all existing mappings in `kernel`:
        for mapping in get_aether_mappings():
            url = kernel_utils.get_mappings_url(mapping['id'])
            url = mapping['url']
            requests.delete(url, headers=headers_testing)
        # In order to be able to fetch this instance of
        # aether.kernel.api.models.Project and
        # aether.kernel.api.models.ProjectSchema, the fixture
        # `/aether-kernel/aether/kernel/api/tests/fixtures/project.json` needs to
        # have been loaded into the kernel database.
        project = requests.get(
            url='http://kernel-test:9000/projects/',
            headers=headers_testing,
        ).json()['results'][0]
        projectschema = requests.get(
            url='http://kernel-test:9000/projectschemas/',
            headers=headers_testing,
        ).json()['results'][0]
        # An example mapping, corresponding to the model
        # `aether.kernel.api.models.Mapping.
        self.example_mapping = {
            'name': 'example',
            'revision': 1,
            'project': project['id'],
            'definition': {
                'mapping': [
                    [
                        '#!uuid',
                        'Person.id'
                    ],
                    [
                        'firstname',
                        'Person.firstName'
                    ],
                    [
                        'lastname',
                        'Person.familyName'
                    ],
                ],
                'entities': {
                    'Person': projectschema['id'],
                }
            }
        }
        # An example document, which will eventually be submitted as `payload`
        # the model `aether.kernel.api.models.Submission`
        self.example_doc = {
            '_id': 'example-aabbbdddccc',
            'deviceId': device_id,
            'firstname': 'Han',
            'lastname': 'Solo',
        }
        url = kernel_utils.get_mappings_url()
        resp = requests.post(url, json=self.example_mapping, headers=headers_testing)
        resp.raise_for_status()
        data = resp.json()
        self.mapping_id = data['id']
        self.mapping_name = data['name']

    def tearDown(self):
        clean_couch()

    @mock.patch('aether.sync.import_couchdb.kernel_utils.test_connection', return_value=False)
    def test_get_surveys_mapping_no_kernel(self, mock_test):
        self.assertRaises(
            RuntimeError,
            get_surveys_mapping,
        )

    def test_get_surveys_mapping(self):
        mapping_names = []
        # Post 30+ surveys to the aether instance, so it starts paginate
        # then we can see that they get mapped right
        while len(mapping_names) < 40:
            url = kernel_utils.get_mappings_url()
            mapping_name = random_string()[:49]
            self.example_mapping['name'] = mapping_name
            response = requests.post(url, json=self.example_mapping, headers=headers_testing)
            self.assertEqual(response.status_code, 201, 'The new survey got created')
            mapping_names.append(mapping_name)

        mapping = get_surveys_mapping()

        # There's gonna be some fixture mappings etc so more than 40
        self.assertGreater(
            len(mapping.keys()),
            len(mapping_names),
            'mapping contains all survey names',
        )
        for mapping_name in mapping_names:
            self.assertIn(mapping_name, mapping)

    @mock.patch('aether.sync.import_couchdb.kernel_utils.test_connection', return_value=False)
    def test_post_to_aether_no_kernel(self, mock_test):
        self.assertRaises(
            RuntimeError,
            post_to_aether,
            document=None,
            mapping=None,
        )

    def test_post_to_aether_non_valid_arguments(self):
        self.assertRaises(
            Exception,
            post_to_aether,
            document={'_id': 'a-b'},
            mapping={},
        )
        self.assertRaises(
            Exception,
            post_to_aether,
            document={'_id': 1},
            mapping={},
        )

    @mock.patch('requests.put')
    @mock.patch('requests.post')
    def test_post_to_aether__without_aether_id(self, mock_post, mock_put):
        post_to_aether(document={'_id': 'a-b'}, mapping={'a': 1}, aether_id=None)
        mock_put.assert_not_called()
        mock_post.assert_called()

    @mock.patch('requests.put')
    @mock.patch('requests.post')
    def test_post_to_aether__with_aether_id(self, mock_post, mock_put):
        post_to_aether(document={'_id': 'a-b'}, mapping={'a': 1}, aether_id=1)
        mock_put.assert_called()
        mock_post.assert_not_called()

    @mock.patch('aether.sync.import_couchdb.import_synced_docs',
                side_effect=Exception('mocked exception'))
    def test_import_one_document_with_error(self, mock_synced):
        # this creates a test couchdb
        device = DeviceDB(device_id=device_id)
        device.save()
        create_db(device_id)

        resp = couchdb.put('{}/{}'.format(device.db_name, self.example_doc['_id']),
                           json=self.example_doc)
        self.assertEqual(resp.status_code, 201, 'The example document got created')

        results = import_synced_devices()
        mock_synced.assert_called()
        self.assertNotEqual(results[0]['error'], None)
        self.assertEqual(results[0]['stats'], None)

    @mock.patch('aether.sync.import_couchdb.post_to_aether',
                side_effect=Exception('mocked exception'))
    def test_import_one_document_with_with_error_in_kernel(self, mock_post):
        # this creates a test couchdb
        device = DeviceDB(device_id=device_id)
        device.save()
        create_db(device_id)

        resp = couchdb.put('{}/{}'.format(device.db_name, self.example_doc['_id']),
                           json=self.example_doc)
        self.assertEqual(resp.status_code, 201, 'The example document got created')

        results = import_synced_devices()
        mock_post.assert_called()
        self.assertNotEqual(results[0]['error'], None)
        self.assertEqual(results[0]['stats'], None)

    def test_import_one_document(self):
        # this creates a test couchdb
        device = DeviceDB(device_id=device_id)
        device.save()
        create_db(device_id)

        resp = couchdb.put('{}/{}'.format(device.db_name, self.example_doc['_id']),
                           json=self.example_doc)
        self.assertEqual(resp.status_code, 201, 'The example document got created')

        import_synced_devices()

        data = get_aether_submissions(self.mapping_id)
        posted = data[0]  # Aether responds with the latest post first

        self.assertEqual(
            posted['mapping'],
            self.mapping_id,
            'Survey posted to the correct id',
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
        device = DeviceDB(device_id=device_id)
        device.save()
        create_db(device_id)

        resp = couchdb.put('{}/{}'.format(device.db_name, self.example_doc['_id']),
                           json=self.example_doc)
        self.assertEqual(resp.status_code, 201, 'The example document got created')

        import_synced_devices()

        # reset the user to test the meta doc mechanism
        device.last_synced_seq = 0
        device.save()

        import_synced_devices()

        docs = get_aether_submissions(self.mapping_id)
        self.assertEqual(len(docs), 1, 'Document is not imported a second time')

    def test_update_document(self):
        # this creates a test couchdb
        device = DeviceDB(device_id=device_id)
        device.save()
        create_db(device_id)

        doc_url = '{}/{}'.format(device.db_name, self.example_doc['_id'])

        resp = couchdb.put(doc_url, json=self.example_doc)
        self.assertEqual(resp.status_code, 201, 'The example document got created')

        import_synced_devices()

        docs = get_aether_submissions(self.mapping_id)
        submission_id = docs[0]['id']

        doc_to_update = couchdb.get(doc_url).json()
        doc_to_update['firstname'] = 'Rey'
        doc_to_update['lastname'] = '(Unknown)'
        resp = couchdb.put(doc_url, json=doc_to_update)
        self.assertEqual(resp.status_code, 201, 'The example document got updated')

        import_synced_devices()

        updated = get_aether_submissions(self.mapping_id)[0]
        self.assertEqual(updated['id'], submission_id, 'updated same doc')
        self.assertEqual(
            updated['payload']['_id'],
            self.example_doc['_id'],
            'updated mapping submission',
        )
        self.assertEqual(updated['payload']['firstname'], 'Rey', 'updated mapping submission')
        self.assertEqual(updated['payload']['lastname'], '(Unknown)', 'updated mapping submission')

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
        device = DeviceDB(device_id=device_id)
        device.save()
        create_db(device_id)

        doc_url = '{}/{}'.format(device.db_name, self.example_doc['_id'])

        resp = couchdb.put(doc_url, json=self.example_doc)
        self.assertEqual(resp.status_code, 201, 'The example document got created')

        # raise error sending docs to Aether Kernel
        with mock.patch('aether.sync.import_couchdb.post_to_aether',
                        return_value=MockHTTPErrorResponse()) as mock_post_to_aether:
            import_synced_devices()
            mock_post_to_aether.assert_called()

        docs = get_aether_submissions(self.mapping_id)
        self.assertEqual(len(docs), 0, 'doc did not get imported to aether')
        status = get_meta_doc(device.db_name, self.example_doc['_id'])

        self.assertIn('error', status, 'posts error key')
        self.assertNotIn('last_rev', status, 'no last rev key')
        self.assertNotIn('aether_id', status, 'no aether id key')
        self.assertIn('http-error', status['error'], 'saves error object')
