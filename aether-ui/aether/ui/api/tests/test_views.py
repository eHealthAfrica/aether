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

INPUT_SAMPLE = {
    'name': 'John',
    'surname': 'Smith',
    'age': 33,
}

ENTITY_SAMPLE = {
    'name': 'Person',
    'type': 'record',
    'fields': [
        {
            'name': 'id',
            'type': 'string',
        },
        {
            'name': 'firstName',
            'type': 'string',
        }
    ],
}


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

    def test_view___pipeline___publish(self):
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
        self.assertEqual(response.status_code, 200)
        pipeline = Pipeline.objects.get(pk=pipeline_id)
        contract = Contract.objects.get(pk=contract_id)
        self.assertEqual(len(contract.kernel_refs), 5)
        self.assertEqual(len(contract.kernel_refs['schemas']), 2)

        response = self.client.post(url, {'project_name': 'Aux', 'contract_id': contract_id})
        response_data = json.loads(response.content)
        self.assertGreater(len(response_data['exists']), 0)

        original_schema = pipeline.schema
        pipeline.schema = ENTITY_SAMPLE
        pipeline.save()
        outcome = utils.publish_preflight(contract)
        self.assertEqual(len(outcome['error']), 0)
        self.assertEqual(len(outcome['exists']), 4)
        self.assertTrue('Pipeline Example' in outcome['exists'][3])
        self.assertIn('Input data will be changed', outcome['exists'][3]['Pipeline Example'])

        pipeline.schema = original_schema
        pipeline.save()

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
            'entity_types': [
                {
                    'name': 'Screening',
                    'type': 'record',
                    'fields': [
                        {'name': 'id', 'type': 'string'},
                        {'name': 'firstName', 'type': 'string'}
                    ]
                }
            ]
        })
        response = self.client.post(url, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        contract_id = response_data['id']
        contract3 = Contract.objects.get(pk=contract_id)
        contract3.kernel_refs = contract.kernel_refs
        contract3.save()

        url = reverse('pipeline-publish', args=[str(pipeline_id) + 'wrong'])
        response = self.client.post(url, {'project_name': 'Aux 1'})
        response_data = json.loads(response.content)
        self.assertIn('is not a valid UUID', response_data['error'][0])

        outcome = utils.publish_preflight(contract)
        self.assertEqual(len(outcome['exists']), 4)

        pipeline.mappingset = 'c29811a0-ff8a-492f-a858-c6b7299c9de7'
        pipeline.save()
        outcome = utils.publish_preflight(contract)

    def test_view_pipeline__publish(self):
        pipeline = Pipeline.objects.create(
            name='Pipeline Mock 2',
            schema={
                'name': 'test',
                'type': 'record',
                'fields': [
                    {
                        'name': 'name',
                        'type': 'string'
                    }
                ]
            },
            input={
                'test': {
                    'name': 'myValue'
                }
            },
        )
        contract = Contract.objects.create(
            entity_types=[
                {
                    'name': 'Test',
                    'type': 'record',
                    'fields': [
                        {
                            'type': 'string',
                            'name': 'name'
                        },
                        {
                            'type': 'string',
                            'name': 'id'
                        }
                    ]
                }
            ],
            mapping=[
                {
                    'source': 'test.name',
                    'destination': 'Test.name'
                },
                {
                    'source': '#!uuid',
                    'destination': 'Test.id'
                }
            ],
            output={
                'id': 'uuids',
                'name': 'a-name'
            },
            pipeline=pipeline,
        )
        outcome = utils.publish_pipeline('Aux', contract, {})
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
        self.assertEqual(len(response_data), 4)
        self.assertEqual(len(response_data[1]['contracts'][0]['entity_types']), 2)

        # Ensure linked mappings are not recreated
        response = self.client.post(url, content_type='application/json')
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 4)

    def test_view_get_kernel_url(self):
        url = reverse('kernel-url')
        response = self.client.get(url)
        self.assertEqual(json.loads(response.content), os.environ.get('AETHER_KERNEL_URL_TEST'))

    def test__pipeline_readonly__update(self):
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
            input=INPUT_SAMPLE
        )
        contract = Contract.objects.create(
            entity_types=[ENTITY_SAMPLE],
            mapping=[
                {'source': '#!uuid', 'destination': 'Person.id'},
                {'source': '$.surname', 'destination': 'Person.firstName'},
            ],
            pipeline=pipeline,
            is_read_only=True,
        )
        url = reverse('pipeline-detail', kwargs={'pk': str(pipeline.pk)})
        INPUT_SAMPLE['weight'] = 45
        data = {
            'input': INPUT_SAMPLE,
            'schema': ENTITY_SAMPLE,
            'mappingset': '503f57a5-2765-400f-9c7c-c2b24b6caed5',
            'name': 'pipeline updated'
        }
        response = self.client.patch(url, data=json.dumps(data), content_type='application/json')
        response_data = json.loads(response.content)
        self.assertTrue('description' in response_data)
        self.assertEqual('Input is readonly', response_data['description'])

        url = reverse('contract-detail', kwargs={'pk': str(contract.pk)})
        response = self.client.patch(url, data=json.dumps({'is_read_only': False}), content_type='application/json')
        url = reverse('pipeline-detail', kwargs={'pk': str(pipeline.pk)})
        response = self.client.patch(url, data=json.dumps(data), content_type='application/json')
        response_data = json.loads(response.content)
        self.assertEqual(str(contract.pk), response_data['contracts'][0]['id'])

    def test_pipeline_publish_exceptions(self):
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
            input=INPUT_SAMPLE
        )
        contract = Contract.objects.create(
            entity_types=[ENTITY_SAMPLE],
            mapping=[
                {'source': '#!uuid', 'destination': 'Person.id'},
                {'source': '$.surname', 'destination': 'Person.firstName'},
            ],
            pipeline=pipeline,
        )
        url = reverse('pipeline-publish', args=[str(pipeline.id)])
        with mock.patch('aether.ui.api.utils.publish_pipeline', side_effect={'error': 'test error'}) as m:
            response = self.client.post(url, {'project_name': 'Aux', 'contract_id': str(contract.pk)})
            self.assertEquals(response.status_code, 400)
            m.assert_called()

        with mock.patch('requests.get') as m:
            m.side_effect = Exception()
            response = utils.publish_pipeline('Aux', contract, {})

        pipeline2 = Pipeline.objects.create(
            name='Pipeline 2 test',
            input=INPUT_SAMPLE
        )
        contract2 = Contract.objects.create(
            entity_types=[ENTITY_SAMPLE],
            mapping=[
                {'source': '#!uuid', 'destination': 'Person.id'},
                {'source': '$.surname', 'destination': 'Person.firstName'},
            ],
            pipeline=pipeline2,
            name='contract 2 test',
        )
        url = reverse('pipeline-publish', args=[str(pipeline2.id)])
        self.client.post(url, {'project_name': 'Aux', 'contract_id': str(contract2.pk)})
        pipeline2 = Pipeline.objects.get(pk=str(pipeline2.pk))
        self.assertTrue(pipeline2.mappingset is not None)
        self.client.post(url, {'project_name': 'Aux', 'overwrite': True, 'contract_id': str(contract2.pk)})
        pipeline2.mappingset = 'bbe75fc8-2eba-45f6-9e19-3087cfdc58c2'
        pipeline2.save()
        response = self.client.post(url, {'project_name': 'Aux', 'overwrite': True, 'contract_id': str(contract2.pk)})
        response_data = json.loads(response.content)
        self.assertEqual(response_data['mappingset'], 'bbe75fc8-2eba-45f6-9e19-3087cfdc58c2')

        contract2 = Contract.objects.get(pk=contract2.pk)
        orginial_project = contract2.kernel_refs['project']
        contract2.kernel_refs['project'] = 'bbe75fc8-2eba-45f6-9e19-3087cfdc58c2'
        contract2.save()
        response = self.client.post(url, {'project_name': 'Aux', 'overwrite': True, 'contract_id': str(contract2.pk)})
        contract2 = Contract.objects.get(pk=contract2.pk)
        self.assertEqual(contract2.kernel_refs['project'], orginial_project)

        pipeline_empty = Pipeline.objects.create(
            name='pipeline empty',
        )
        contract_empty = Contract.objects.create(
            entity_types=[],
            mapping=[],
            pipeline=pipeline_empty,
            name='contract empty',
        )
        outcome = utils.publish_pipeline('Aux', contract_empty)
        self.assertTrue('artefacts' in outcome)
