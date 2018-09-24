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

import json
import mock
import os

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TransactionTestCase

from . import (PIPELINE_EXAMPLE, PIPELINE_EXAMPLE_WITH_MAPPING_ERRORS,
               CONTRACT_EXAMPLE, CONTRACT_EXAMPLE_WITH_MAPPING_ERRORS)

from ..models import Pipeline, Contract
from .. import utils


RESPONSE_MOCK = mock.Mock(status_code=200)
APP_TOKEN_MOCK = mock.Mock(base_url='http://test', token='ABCDEFGH')


class ViewsTest(TransactionTestCase):

    def setUp(self):
        username = 'test'
        email = 'test@example.com'
        password = 'testtest'
        get_user_model().objects.create_user(username, email, password)
        self.assertTrue(self.client.login(username=username, password=password))

    def tearDown(self):
        self.client.logout()

    def test__pipeline__viewset(self):
        url = reverse('pipeline-list')
        data = json.dumps({'name': 'Pipeline'})
        response = self.client.post(url, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        pipeline_id = response_data['id']
        self.assertEqual(response_data['name'], 'Pipeline')

        url = reverse('contract-list')
        data = json.dumps({'name': 'Contract', 'pipeline': pipeline_id})
        contract_response = self.client.post(url, data=data, content_type='application/json')
        contract_response_data = json.loads(contract_response.content)
        self.assertEqual(contract_response_data['name'], 'Contract')
        # initial status without meaningful data
        self.assertEqual(len(contract_response_data['mapping_errors']), 0)
        self.assertEqual(len(contract_response_data['output']), 0)

        url_patch = reverse('pipeline-detail', kwargs={'pk': pipeline_id})

        # patching a property will not alter the rest

        data = json.dumps({'input': {'id': 1}})
        response = self.client.patch(url_patch, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        self.assertEqual(response_data['name'], 'Pipeline', 'Preserves name')
        self.assertEqual(response_data['input'], {'id': 1}, 'Sets input')

        data = json.dumps({'name': 'Pipeline 2'})
        response = self.client.patch(url_patch, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        self.assertEqual(response_data['name'], 'Pipeline 2', 'Changes name')
        self.assertEqual(response_data['input'], {'id': 1}, 'Preserves input')

    def test_view_pipeline___publish(self):
        url = reverse('pipeline-list')
        data = json.dumps(PIPELINE_EXAMPLE)
        response = self.client.post(url, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        pipeline_id = response_data['id']
        self.assertEqual(response_data['name'], 'Pipeline Example')
        url = reverse('contract-list')
        CONTRACT_EXAMPLE['pipeline'] = pipeline_id
        data = json.dumps(CONTRACT_EXAMPLE)
        response = self.client.post(url, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        contract_id = response_data['id']
        url = reverse('pipeline-publish', args=[pipeline_id])
        response = self.client.post(url, {'project_name': 'Aux', 'contract_id': contract_id})
        response_data = json.loads(response.content)

        # make sure kernel db is clean for this to pass
        self.assertEqual(response.status_code, 200)
        pipeline = Pipeline.objects.get(pk=pipeline_id)
        contract = Contract.objects.get(pk=contract_id)
        self.assertEqual(len(contract.kernel_refs), 5)
        self.assertEqual(len(contract.kernel_refs['schemas']), 2)

        outcome = {
                    'successful': [],
                    'error': [],
                    'exists': [],
                    'ids': {
                        'mapping': {},
                        'schema': {},
                    }
                }
        outcome = utils.publish_preflight(pipeline, 'Aux', outcome, contract)
        self.assertEqual(len(outcome['error']), 0)
        self.assertEqual(len(outcome['exists']), 3)

        url = reverse('pipeline-list')
        data = json.dumps(PIPELINE_EXAMPLE_WITH_MAPPING_ERRORS)
        response = self.client.post(url, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        pipeline_id = response_data['id']

        url = reverse('contract-list')
        CONTRACT_EXAMPLE_WITH_MAPPING_ERRORS['pipeline'] = pipeline_id
        data = json.dumps(CONTRACT_EXAMPLE_WITH_MAPPING_ERRORS)
        response = self.client.post(url, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        contract_id = response_data['id']

        url = reverse('pipeline-publish', args=[pipeline_id])
        response = self.client.post(url, {'contract_id': contract_id})
        response_data = json.loads(response.content)
        self.assertIn('mappings have errors', response_data['error'][0])

        url = reverse('pipeline-list')
        data = json.dumps({
            'name': 'pipeline1'
        })
        response = self.client.post(url, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        pipeline_id = response_data['id']
        url = reverse('contract-list')
        data = json.dumps({
            'name': 'contract1',
            'pipeline': pipeline_id
        })
        response = self.client.post(url, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        contract_id = response_data['id']
        contract2 = Contract.objects.get(pk=contract_id)
        contract2.kernel_refs = contract.kernel_refs
        contract2.save()

        url = reverse('pipeline-publish', args=[pipeline_id])
        response = self.client.post(url, {'project_name': 'Aux 1', 'contract_id': contract_id})
        response_data = json.loads(response.content)
        self.assertGreater(len(response_data['exists']), 0)
        map_data = json.loads(data)
        self.assertIn(response_data['exists'][0][map_data['name']],
                      'Mapping with id {} exists'.format(contract.kernel_refs['mappings']))

        url = reverse('pipeline-list')
        data = json.dumps({
            'name': 'pipeline 2'
        })
        response = self.client.post(url, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        pipeline_id = response_data['id']
        url = reverse('contract-list')
        data = json.dumps({
            'name': 'contract 2',
            'pipeline': pipeline_id,
            'entity_types': [{'name': 'Screening', 'type': 'record', 'fields':
                             [
                                {'name': 'id', 'type': 'string'},
                                {'name': 'firstName', 'type': 'string'}
                             ]
                        }]
        })
        response = self.client.post(url, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        contract_id = response_data['id']
        contract3 = Contract.objects.get(pk=contract_id)
        contract3.kernel_refs = contract.kernel_refs
        contract3.save()
        url = reverse('pipeline-publish', args=[pipeline_id])
        response = self.client.post(url, {'project_name': 'Aux 1', 'contract_id': contract_id})
        response_data = json.loads(response.content)
        self.assertGreater(len(response_data['exists']), 0)
        self.assertIn(response_data['exists'][0]['Screening'],
                      '{} schema with id {} exists'.format('Screening',
                                                           contract3.kernel_refs['schemas']['Screening']))

        url = reverse('pipeline-publish', args=[str(pipeline_id) + 'wrong'])
        response = self.client.post(url, {'project_name': 'Aux 1'})
        response_data = json.loads(response.content)
        self.assertIn('is not a valid UUID', response_data['error'][0])
        outcome = {
                    'successful': [],
                    'error': [],
                    'exists': [],
                    'ids': {
                        'mapping': {},
                        'schema': {},
                    }
                }
        outcome = utils.publish_preflight(pipeline, 'Aux', outcome, contract)
        self.assertEqual(len(outcome['exists']), 3)

    def test_view_pipeline__publish(self):
        pipeline = Pipeline.objects.create(
            name='Pipeline Mock 2',
            schema={'name': 'test', 'type': 'record', 'fields':
                    [{'name': 'name', 'type': 'string'}]},
            input={'test': {'name': 'myValue'}},
        )
        contract = Contract.objects.create(
            entity_types=[{'name': 'Test', 'type': 'record', 'fields':
                          [{'type': 'string', 'name': 'name'}, {'type': 'string', 'name': 'id'}]}],
            mapping=[{'source': 'test.name', 'destination': 'Test.name'},
                     {'source': '#!uuid', 'destination': 'Test.id'}],
            output={'id': 'uuids', 'name': 'a-name'},
            pipeline=pipeline,
        )
        outcome = utils.publish_pipeline(pipeline, 'Aux', contract, {})
        self.assertTrue('artefacts' in outcome)
        url = reverse('pipeline-publish', args=[str(pipeline.id)])
        response = self.client.post(url, {'project_name': 'Aux', 'overwrite': True, 'contract_id': str(contract.pk)})
        response_data = json.loads(response.content)
        self.assertTrue('contracts' in response_data)
        self.assertEqual(len(response_data['contracts']), 1)
        contract = Contract.objects.get(pk=contract.pk)
        self.assertTrue('project' in contract.kernel_refs)

        contract.kernel_refs = {}
        contract.save()
        response = self.client.post(url, {'project_name': 'Aux', 'contract_id': str(contract.pk)})
        response_data = json.loads(response.content)
        self.assertTrue(len(response_data['exists']), 2)
        contract = Contract.objects.get(pk=contract.pk)
        self.assertFalse('project' in contract.kernel_refs)

    def test_view_pipeline_fetch(self):
        url = reverse('pipeline-fetch')
        response = self.client.post(url, content_type='application/json')
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 2)
        self.assertEqual(len(response_data[0]['contracts'][0]['entity_types']), 2)

        # Ensure linked mappings are not recreated]
        response = self.client.post(url, content_type='application/json')
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 2)

    def test_view_get_kernel_url(self):
        url = reverse('kernel-url')
        response = self.client.get(url)
        self.assertEqual(json.loads(response.content), os.environ.get('AETHER_KERNEL_URL_TEST'))
