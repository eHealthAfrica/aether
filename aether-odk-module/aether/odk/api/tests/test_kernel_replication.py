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

import json
import mock
import requests

from . import CustomTestCase, MockResponse
from ..kernel_replication import (
    replicate_project,
    replicate_xform,
    KernelReplicationError,
    __upsert_item as upsert,

    # from aether common
    get_auth_header,
    get_kernel_server_url,
)


class KernelReplicationTest(CustomTestCase):

    @mock.patch('aether.odk.api.kernel_replication.get_auth_header', return_value=None)
    def test__upsert_item__no_connection(self, mock_auth):
        with self.assertRaises(KernelReplicationError) as kre:
            upsert(
                item_model='none',
                item_id=1,
                item_new={},
            )

        self.assertIsNotNone(kre)
        self.assertIn('Connection with Aether Kernel server is not possible.',
                      str(kre.exception), kre)
        mock_auth.assert_called_once()

    @mock.patch('requests.get', return_value=mock.Mock(status_code=400))
    @mock.patch('aether.odk.api.kernel_replication.get_auth_header', return_value={
        'Authorization': 'Token ABCDEFGH'
    })
    def test__upsert_item__unexpected_error(self, mock_auth, mock_get):
        with self.assertRaises(KernelReplicationError) as kre:
            upsert(
                item_model='projects',
                item_id=1,
                item_new={},
            )

        self.assertIsNotNone(kre)
        self.assertIn('Unexpected response from Aether Kernel server',
                      str(kre.exception), kre)
        self.assertIn('while trying to check the existence of the project with id 1',
                      str(kre.exception), kre)
        mock_auth.assert_called_once()
        mock_get.assert_called_once_with(
            url='http://kernel-test:9000/projects/1.json',
            headers={'Authorization': 'Token ABCDEFGH'},
        )

    @mock.patch('requests.get', return_value=mock.Mock(status_code=200))
    @mock.patch('aether.odk.api.kernel_replication.get_auth_header', return_value={
        'Authorization': 'Token ABCDEFGH'
    })
    def test__upsert_item__already_there__no_update(self, mock_auth, mock_get):
        self.assertTrue(upsert(item_model='projects', item_id=1, item_new={}))

        mock_auth.assert_called_once()
        mock_get.assert_called_once_with(
            url='http://kernel-test:9000/projects/1.json',
            headers={'Authorization': 'Token ABCDEFGH'},
        )

    @mock.patch('requests.put', return_value=mock.Mock(status_code=200))
    @mock.patch('requests.get', side_effect=[MockResponse(status_code=200, json_data={'id': '1'})])
    @mock.patch('aether.odk.api.kernel_replication.get_auth_header', return_value={
        'Authorization': 'Token ABCDEFGH'
    })
    def test__upsert_item__already_there__with_update(self, mock_auth, mock_get, mock_put):
        self.assertTrue(upsert(item_model='projects',
                               item_id=1,
                               item_new={},
                               item_update={
                                   'name': 'new',
                               },
                               ))

        mock_auth.assert_called_once()
        mock_get.assert_called_once_with(
            url='http://kernel-test:9000/projects/1.json',
            headers={'Authorization': 'Token ABCDEFGH'},
        )
        mock_put.assert_called_once_with(
            url='http://kernel-test:9000/projects/1.json',
            headers={'Authorization': 'Token ABCDEFGH'},
            json={'id': '1', 'name': 'new'},
        )

    @mock.patch('requests.put', return_value=mock.Mock(status_code=400))
    @mock.patch('requests.get', side_effect=[MockResponse(status_code=200, json_data={'id': '1'})])
    @mock.patch('aether.odk.api.kernel_replication.get_auth_header', return_value={
        'Authorization': 'Token ABCDEFGH'
    })
    def test__upsert_item__already_there__with_update__error(self, mock_auth, mock_get, mock_put):
        with self.assertRaises(KernelReplicationError) as kre:
            upsert(item_model='projects',
                   item_id=1,
                   item_new={},
                   item_update={'name': 'update'},
                   )
        self.assertIsNotNone(kre)
        self.assertIn('Unexpected response from Aether Kernel server',
                      str(kre.exception), kre)
        self.assertIn('while trying to update the project with id 1',
                      str(kre.exception), kre)

        mock_auth.assert_called_once()
        mock_get.assert_called_once_with(
            url='http://kernel-test:9000/projects/1.json',
            headers={'Authorization': 'Token ABCDEFGH'},
        )
        mock_put.assert_called_once_with(
            url='http://kernel-test:9000/projects/1.json',
            headers={'Authorization': 'Token ABCDEFGH'},
            json={'id': '1', 'name': 'update'},
        )

    @mock.patch('requests.post', return_value=mock.Mock(status_code=400))
    @mock.patch('requests.get', return_value=mock.Mock(status_code=404))
    @mock.patch('aether.odk.api.kernel_replication.get_auth_header', return_value={
        'Authorization': 'Token ABCDEFGH'
    })
    def test__upsert_item__not_there__with_create__error(self, mock_auth, mock_get, mock_post):
        with self.assertRaises(KernelReplicationError) as kre:
            upsert(item_model='projects',
                   item_id=1,
                   item_new={'name': 'new'},
                   )
        self.assertIsNotNone(kre)
        self.assertIn('Unexpected response from Aether Kernel server',
                      str(kre.exception), kre)
        self.assertIn('while trying to create the project with id 1',
                      str(kre.exception), kre)

        mock_auth.assert_called_once()
        mock_get.assert_called_once_with(
            url='http://kernel-test:9000/projects/1.json',
            headers={'Authorization': 'Token ABCDEFGH'},
        )
        mock_post.assert_called_once_with(
            url='http://kernel-test:9000/projects.json',
            headers={'Authorization': 'Token ABCDEFGH'},
            json={'name': 'new'},
        )

    @mock.patch('requests.post', return_value=mock.Mock(status_code=201))
    @mock.patch('requests.get', return_value=mock.Mock(status_code=404))
    @mock.patch('aether.odk.api.kernel_replication.get_auth_header', return_value={
        'Authorization': 'Token ABCDEFGH'
    })
    def test__upsert_item__not_there(self, mock_auth, mock_get, mock_post):
        self.assertTrue(
            upsert(item_model='projects',
                   item_id=1,
                   item_new={'name': 'new'},
                   ))

        mock_auth.assert_called_once()
        mock_get.assert_called_once_with(
            url='http://kernel-test:9000/projects/1.json',
            headers={'Authorization': 'Token ABCDEFGH'},
        )
        mock_post.assert_called_once_with(
            url='http://kernel-test:9000/projects.json',
            headers={'Authorization': 'Token ABCDEFGH'},
            json={'name': 'new'},
        )


class AetherKernelReplicationTest(CustomTestCase):

    def setUp(self):
        super(AetherKernelReplicationTest, self).setUp()

        # create xForm entry
        self.xform = self.helper_create_xform(
            xml_data=self.samples['xform']['raw-xml'],
        )
        self.project = self.xform.project

        self.KERNEL_HEADERS = get_auth_header()
        kernel_url = get_kernel_server_url()
        self.PROJECT_URL = f'{kernel_url}/projects/{str(self.project.project_id)}.json'
        self.MAPPING_URL = f'{kernel_url}/mappings/{str(self.xform.kernel_id)}.json'
        self.SCHEMA_URL = f'{kernel_url}/schemas/{str(self.xform.kernel_id)}.json'
        self.PROJECTSCHEMA_URL = f'{kernel_url}/projectschemas/{str(self.xform.kernel_id)}.json'

        # check that nothing exists already in kernel
        response = requests.get(self.PROJECT_URL, headers=self.KERNEL_HEADERS)
        self.assertEqual(response.status_code, 404)
        response = requests.get(self.MAPPING_URL, headers=self.KERNEL_HEADERS)
        self.assertEqual(response.status_code, 404)
        response = requests.get(self.SCHEMA_URL, headers=self.KERNEL_HEADERS)
        self.assertEqual(response.status_code, 404)
        response = requests.get(self.PROJECTSCHEMA_URL, headers=self.KERNEL_HEADERS)
        self.assertEqual(response.status_code, 404)

    def tearDown(self):
        super(AetherKernelReplicationTest, self).tearDown()

        # delete the test objects created in kernel testing server
        requests.delete(self.PROJECT_URL, headers=self.KERNEL_HEADERS)
        requests.delete(self.SCHEMA_URL, headers=self.KERNEL_HEADERS)

    def test__replicate_project(self):

        self.assertTrue(replicate_project(self.project))

        response = requests.get(self.PROJECT_URL, headers=self.KERNEL_HEADERS)
        self.assertEqual(response.status_code, 200)
        kernel_project = json.loads(response.content.decode('utf-8'))
        self.assertEqual(kernel_project['id'], str(self.project.project_id))
        self.assertNotEqual(kernel_project['name'], self.project.name)

    def test__replicate_xform(self):

        self.assertTrue(replicate_xform(self.xform))

        response = requests.get(self.PROJECT_URL, headers=self.KERNEL_HEADERS)
        self.assertEqual(response.status_code, 200)
        kernel_project = json.loads(response.content.decode('utf-8'))
        self.assertEqual(kernel_project['id'], str(self.project.project_id))

        response = requests.get(self.MAPPING_URL, headers=self.KERNEL_HEADERS)
        self.assertEqual(response.status_code, 200)
        kernel_mapping = json.loads(response.content.decode('utf-8'))
        self.assertEqual(kernel_mapping['id'], str(self.xform.kernel_id))

        response = requests.get(self.SCHEMA_URL, headers=self.KERNEL_HEADERS)
        self.assertEqual(response.status_code, 200)
        kernel_schema = json.loads(response.content.decode('utf-8'))
        self.assertEqual(kernel_schema['id'], str(self.xform.kernel_id))

        response = requests.get(self.PROJECTSCHEMA_URL, headers=self.KERNEL_HEADERS)
        self.assertEqual(response.status_code, 200)
        kernel_projectschema = json.loads(response.content.decode('utf-8'))
        self.assertEqual(kernel_projectschema['id'], str(self.xform.kernel_id))
