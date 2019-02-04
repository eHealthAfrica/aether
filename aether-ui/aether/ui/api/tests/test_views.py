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
import uuid

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TransactionTestCase

from . import (PIPELINE_EXAMPLE, PIPELINE_EXAMPLE_WITH_ERRORS,
               CONTRACT_EXAMPLE, CONTRACT_EXAMPLE_WITH_ERRORS)

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

        # save the list of project and schema ids created by the test
        # to remove them in the tearDown method
        self.project_ids = set()
        self.schema_ids = set()

    def tearDown(self):
        # cleaning kernel
        for pk in self.project_ids:
            self.helper__delete_in_kernel('projects', pk)
        for pk in self.schema_ids:
            self.helper__delete_in_kernel('schemas', pk)

        self.client.logout()

    def helper__delete_in_kernel(self, model, pk):
        try:
            utils.kernel_data_request(f'{model}/{pk}/', 'delete')
        except Exception:
            pass  # ignore

    def helper__publish(self, pipeline_id, contract_id, **kwargs):
        # use this method to publish to kernel
        # it will gather the created artefact ids and wipe them after the tests
        response = self.client.post(
            reverse('pipeline-publish', args=[pipeline_id]),
            {'contract_id': contract_id, **kwargs})

        try:
            # try to get the kernel artefacts
            contract = Contract.objects.get(pk=contract_id)
            if contract.kernel_refs:
                if contract.kernel_refs.get('project'):
                    self.project_ids.add(contract.kernel_refs['project'])
                if contract.kernel_refs.get('schemas'):
                    self.schema_ids.update(contract.kernel_refs['schemas'].values())
        except Exception:
            pass  # just ignore

        return response

    def test__get_kernel_url(self):
        url = reverse('kernel-url')
        response = self.client.get(url)
        self.assertEqual(
            json.loads(response.content),
            os.environ.get('AETHER_KERNEL_URL_TEST')
        )

    def test__pipeline__fetch(self):
        # create the pipeline
        response = self.client.post(
            reverse('pipeline-list'),
            data=json.dumps(PIPELINE_EXAMPLE),
            content_type='application/json'
        )
        pipeline_id = json.loads(response.content)['id']

        # create the contract
        CONTRACT_EXAMPLE['pipeline'] = pipeline_id
        response = self.client.post(
            reverse('contract-list'),
            data=json.dumps(CONTRACT_EXAMPLE),
            content_type='application/json'
        )
        contract_id = json.loads(response.content)['id']

        # publish the contract
        self.helper__publish(pipeline_id, contract_id, project_name='Fetching #1')

        # delete pipeline and contract and fetch them back from kernel
        Pipeline.objects.all().delete()
        self.assertEqual(Pipeline.objects.count(), 0)
        self.assertEqual(Contract.objects.count(), 0)

        url = reverse('pipeline-fetch')
        response = self.client.post(url, content_type='application/json')
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 1, response_data)
        self.assertEqual(len(response_data[0]['contracts'][0]['entity_types']), 2)
        self.assertEqual(Pipeline.objects.count(), 1)
        self.assertEqual(Contract.objects.count(), 1)

        # Ensure kernel artefacts are not recreated twice
        response = self.client.post(url, content_type='application/json')
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 1, response_data)
        self.assertEqual(Pipeline.objects.count(), 1)
        self.assertEqual(Contract.objects.count(), 1)

        # delete contract and try again
        Contract.objects.all().delete()
        self.assertEqual(Pipeline.objects.count(), 1)
        self.assertEqual(Contract.objects.count(), 0)

        response = self.client.post(url, content_type='application/json')
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 1, response_data)
        self.assertEqual(Pipeline.objects.count(), 1)
        self.assertEqual(Contract.objects.count(), 1)

    def test__pipeline__and__contract__viewsets(self):
        url = reverse('pipeline-list')
        data = json.dumps({'name': 'Pipeline'})
        response = self.client.post(url, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        pipeline_id = response_data['id']
        self.assertEqual(response_data['name'], 'Pipeline')

        # patching a property will not alter the rest
        url_patch = reverse('pipeline-detail', kwargs={'pk': pipeline_id})

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

        # create a linked contract
        url = reverse('contract-list')
        data = json.dumps({'name': 'Contract', 'pipeline': pipeline_id})
        contract_response = self.client.post(url, data=data, content_type='application/json')
        contract_response_data = json.loads(contract_response.content)
        self.assertEqual(contract_response_data['name'], 'Contract')
        # initial status without meaningful data
        self.assertEqual(len(contract_response_data['mapping_errors']), 0)
        self.assertEqual(len(contract_response_data['output']), 0)

    def test__pipeline__readonly__update(self):
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

    def test__pipeline__publish__failure(self):
        # create a pipeline with errors
        url = reverse('pipeline-list')
        data = json.dumps(PIPELINE_EXAMPLE_WITH_ERRORS)
        response = self.client.post(url, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        pipeline_id_with_errors = response_data['id']

        # create a contract with errors
        url = reverse('contract-list')
        CONTRACT_EXAMPLE_WITH_ERRORS['pipeline'] = pipeline_id_with_errors
        data = json.dumps(CONTRACT_EXAMPLE_WITH_ERRORS)
        response = self.client.post(url, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        contract_id_with_errors = response_data['id']

        # try to publish
        response = self.helper__publish(pipeline_id_with_errors, contract_id_with_errors)
        response_data = json.loads(response.content)
        self.assertIn('mappings have errors', response_data['error'][0])

    def test__pipeline__publish__workflow(self):
        # create the pipeline
        url = reverse('pipeline-list')
        data = json.dumps(PIPELINE_EXAMPLE)
        response = self.client.post(url, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        pipeline_id = response_data['id']
        self.assertEqual(response_data['name'], 'Pipeline Example')

        # create the contract
        url = reverse('contract-list')
        CONTRACT_EXAMPLE['pipeline'] = pipeline_id
        data = json.dumps(CONTRACT_EXAMPLE)
        response = self.client.post(url, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        contract_id = response_data['id']

        # publish the contract
        response = self.helper__publish(pipeline_id, contract_id, project_name='Workflow')
        response_data = json.loads(response.content)
        self.assertEqual(response.status_code, 200, response_data)

        contract = Contract.objects.get(pk=contract_id)
        self.assertIn('project', contract.kernel_refs)
        self.assertIn('mapping', contract.kernel_refs)
        self.assertIn('schemas', contract.kernel_refs)
        self.assertIn('PersonY', contract.kernel_refs['schemas'])
        self.assertIn('Screening', contract.kernel_refs['schemas'])

        response = self.helper__publish(pipeline_id, contract_id, project_name='Workflow')
        response_data = json.loads(response.content)
        self.assertGreater(len(response_data['exists']), 0)

        # check `publish_prefight` changing the pipeline schema
        pipeline = Pipeline.objects.get(pk=pipeline_id)
        original_schema = pipeline.schema
        original_input = pipeline.input

        pipeline.schema = ENTITY_SAMPLE
        pipeline.input = INPUT_SAMPLE
        pipeline.save()

        outcome = utils.publish_preflight(contract)
        self.assertEqual(len(outcome['successful']), 0, outcome['successful'])
        self.assertEqual(len(outcome['error']), 0, outcome['error'])
        self.assertEqual(len(outcome['exists']), 5, outcome['exists'])
        self.assertIn('Pipeline Example', outcome['exists'][3])
        self.assertIn('Input data will be changed', outcome['exists'][3]['Pipeline Example'], outcome)
        self.assertIn('Schema data will be changed', outcome['exists'][4]['Pipeline Example'], outcome)

        pipeline.schema = original_schema
        pipeline.input = original_input
        pipeline.save()

        # create a new pipeline
        url = reverse('pipeline-list')
        data = json.dumps({
            'name': 'pipeline 2'
        })
        response = self.client.post(url, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        pipeline_id_2 = response_data['id']

        # create a new contract with the same kernel_refs as the first one
        url = reverse('contract-list')
        data = json.dumps({
            'name': 'contract 2',
            'pipeline': pipeline_id_2
        })
        response = self.client.post(url, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        contract_id_2 = response_data['id']

        contract2 = Contract.objects.get(pk=contract_id_2)
        contract2.kernel_refs = contract.kernel_refs
        contract2.save()

        # try to publish
        response = self.helper__publish(pipeline_id_2, contract_id_2, project_name='Workflow')
        response_data = json.loads(response.content)
        self.assertGreater(len(response_data['exists']), 0, response_data['exists'])
        self.assertIn(
            response_data['exists'][0]['contract 2'],
            'Contract (mapping) with id {} exists on kernel'.format(contract.kernel_refs['mapping'])
        )

        # another pipeline
        url = reverse('pipeline-list')
        data = json.dumps({
            'name': 'pipeline 3'
        })
        response = self.client.post(url, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        pipeline_id_3 = response_data['id']

        # another contract
        url = reverse('contract-list')
        data = json.dumps({
            'name': 'contract 3',
            'pipeline': pipeline_id_3,
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
        contract_id_3 = response_data['id']
        contract3 = Contract.objects.get(pk=contract_id_3)
        contract3.kernel_refs = contract.kernel_refs
        contract3.save()

        response = self.helper__publish(pipeline_id_3 + '###', contract_id=None)
        response_data = json.loads(response.content)
        self.assertIn('is not a valid UUID', response_data['error'][0])

        outcome = utils.publish_preflight(contract)
        self.assertEqual(len(outcome['exists']), 5, outcome['exists'])

    def test__pipeline__publish__overwrite(self):
        pipeline = Pipeline.objects.create(
            name='Pipeline Test',
            schema={
                'name': 'test',
                'type': 'record',
                'fields': [{'type': 'string', 'name': 'name'}]
            },
            input={'test': {'name': 'myValue'}},
        )
        contract = Contract.objects.create(
            name='Contract Test',
            pipeline=pipeline,
            entity_types=[{
                'name': 'Test',
                'type': 'record',
                'fields': [
                    {'type': 'string', 'name': 'id'},
                    {'type': 'string', 'name': 'name'},
                ]
            }],
            mapping=[
                {'source': '#!uuid', 'destination': 'Test.id'},
                {'source': 'test.name', 'destination': 'Test.name'},
            ],
        )

        pipeline_id = str(pipeline.id)
        contract_id = str(contract.id)
        response = self.helper__publish(pipeline_id, contract_id, project_name='Overwrite')
        response_data = json.loads(response.content)
        self.assertIn('contracts', response_data, response_data)
        self.assertEqual(len(response_data['contracts']), 1)

        response = self.helper__publish(pipeline_id, contract_id, project_name='Overwrite', overwrite=True)
        response_data = json.loads(response.content)
        self.assertIn('contracts', response_data, response_data)
        self.assertEqual(len(response_data['contracts']), 1)

        contract = Contract.objects.get(pk=contract.pk)
        self.assertIn('project', contract.kernel_refs)

        contract.kernel_refs = {}
        contract.save()

        response = self.helper__publish(pipeline_id, contract_id, project_name='Overwrite')
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data['exists']), 2, response_data['exists'])
        self.assertNotIn('project', contract.kernel_refs)

    def test__pipeline__publish__exceptions(self):
        pipeline = Pipeline.objects.create(
            name='Pipeline Exception',
            input=INPUT_SAMPLE,
            schema=ENTITY_SAMPLE,
        )
        contract = Contract.objects.create(
            name='Contract Exception',
            pipeline=pipeline,
            entity_types=[ENTITY_SAMPLE],
            mapping=[
                {'source': '#!uuid', 'destination': 'Person.id'},
                {'source': '$.surname', 'destination': 'Person.firstName'},
            ],
        )

        url = reverse('pipeline-publish', args=[str(pipeline.id)])
        with mock.patch('aether.ui.api.utils.publish_contract', side_effect={'error': 'test error'}) as m:
            response = self.client.post(url, {'project_name': 'Exception', 'contract_id': str(contract.pk)})
            self.assertEquals(response.status_code, 400)
            m.assert_called()

        with mock.patch('requests.get') as m:
            m.side_effect = Exception()
            response = utils.publish_contract('Exception #2', contract, {})

    def test__pipeline__publish__exceptions__2(self):
        pipeline = Pipeline.objects.create(
            name='Pipeline 2 Exception',
            input=INPUT_SAMPLE,
        )
        contract = Contract.objects.create(
            name='Contract Exception 2',
            pipeline=pipeline,
            entity_types=[ENTITY_SAMPLE],
            mapping=[
                {'source': '#!uuid', 'destination': 'Person.id'},
                {'source': '$.surname', 'destination': 'Person.firstName'},
            ],
        )

        pipeline_id = str(pipeline.id)
        contract_id = str(contract.id)
        self.helper__publish(pipeline_id, contract_id, project_name='Exception')

        pipeline.refresh_from_db()
        self.assertIsNotNone(pipeline.mappingset, 'Pipeline has been published')

        # change the linked mappingset+project
        MAPPINGSET_ID = str(uuid.uuid4())
        pipeline.mappingset = MAPPINGSET_ID
        pipeline.save()

        contract.refresh_from_db()
        original_project = contract.kernel_refs['project']
        contract.kernel_refs['project'] = MAPPINGSET_ID
        contract.save()

        response = self.helper__publish(pipeline_id, contract_id, project_name='Exception')
        self.assertEqual(response.status_code, 400, response.content)

        response = self.helper__publish(pipeline_id, contract_id, project_name='Exception', overwrite=True)
        self.assertEqual(response.status_code, 200, response.content)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['mappingset'], MAPPINGSET_ID)

        contract.refresh_from_db()
        self.assertEqual(contract.kernel_refs['project'], original_project, 'takes the previous project id')

        # change the linked mappingset again
        MAPPINGSET_ID_2 = str(uuid.uuid4())
        pipeline.mappingset = MAPPINGSET_ID_2
        pipeline.save()

        response = self.helper__publish(pipeline_id, contract_id, project_name='Exception')
        self.assertEqual(response.status_code, 400, response.content)

        response = self.helper__publish(pipeline_id, contract_id, project_name='Exception', overwrite=True)
        self.assertEqual(response.status_code, 200, response.content)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['mappingset'], MAPPINGSET_ID_2)
