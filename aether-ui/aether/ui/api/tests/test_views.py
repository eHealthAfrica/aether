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

from unittest import mock
import os
import uuid

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TransactionTestCase, override_settings
from requests.exceptions import HTTPError
from rest_framework.response import Response

from ..models import Project, Pipeline, Contract
from ..utils import wrap_kernel_headers


@override_settings(MULTITENANCY=False)
class ViewsTest(TransactionTestCase):

    def setUp(self):
        super(ViewsTest, self).setUp()

        username = 'test'
        email = 'test@example.com'
        password = 'testtest'
        get_user_model().objects.create_user(username, email, password)
        self.assertTrue(self.client.login(username=username, password=password))

    def tearDown(self):
        self.client.logout()
        super(ViewsTest, self).tearDown()

    def test__get_kernel_url(self):
        url = reverse('kernel-url')
        self.assertEqual(url, '/api/kernel-url/')
        response = self.client.get(url)
        self.assertEqual(
            response.json(),
            os.environ.get('AETHER_KERNEL_URL_TEST')
        )

    @mock.patch('aether.ui.api.views.utils.kernel_artefacts_to_ui_artefacts')
    def test__pipeline__fetch(self, mock_kernel):
        url = reverse('pipeline-fetch')
        self.assertEqual(url, '/api/pipelines/fetch/')
        self.client.post(url)
        mock_kernel.assert_called_once()

    def test__contract__publish(self):
        INPUT_SAMPLE = {
            'name': 'John',
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
                    'name': 'name',
                    'type': ['null', 'string'],
                },
            ],
        }

        MAPPING_RULES = [
            {
                'source': '#!uuid',
                'destination': 'Person.id'
            },
        ]

        contract_id = str(uuid.uuid4())

        url = reverse('contract-publish', kwargs={'pk': contract_id})
        self.assertEqual(url, f'/api/contracts/{contract_id}/publish/')

        url_pp = reverse('contract-publish-preflight', kwargs={'pk': contract_id})
        self.assertEqual(url_pp, f'/api/contracts/{contract_id}/publish-preflight/')

        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

        response = self.client.get(url_pp)
        self.assertEqual(response.status_code, 404)

        # create non-publishable contract
        contract = Contract.objects.create(
            pk=contract_id,
            name='Publishing contract',
            pipeline=Pipeline.objects.create(
                name='Publishing pipeline',
                project=Project.objects.create(name='Publishing project'),
                input=INPUT_SAMPLE,
                schema=ENTITY_SAMPLE,
            ),
        )

        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

        response = self.client.get(url_pp)
        self.assertEqual(response.status_code, 200, 'Publish preflight does not raise errors')

        contract.entity_types = [ENTITY_SAMPLE, ]
        contract.mapping_rules = MAPPING_RULES
        contract.save()

        with mock.patch('aether.ui.api.views.utils.publish_contract') as mock_publish:
            response = self.client.post(url)
            self.assertEqual(response.status_code, 200)
            mock_publish.assert_called_once()

        with mock.patch('aether.ui.api.views.utils.publish_preflight', return_value={}) as mock_publish:
            response = self.client.get(url_pp)
            self.assertEqual(response.status_code, 200)
            mock_publish.assert_called_once()

    def test__published_contract__delete(self):
        INPUT_SAMPLE = {
            'name': 'John',
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
                    'name': 'name',
                    'type': ['null', 'string'],
                },
            ],
        }

        MAPPING_RULES = [
            {
                'source': '#!uuid',
                'destination': 'Person.id'
            },
        ]
        pipeline = Pipeline.objects.create(
            name='Delete pipeline',
            project=Project.objects.create(name='Delete project'),
            input=INPUT_SAMPLE,
            schema=ENTITY_SAMPLE,
        )
        contract = Contract.objects.create(
            name='Delete contract',
            pipeline=pipeline,
            entity_types=[ENTITY_SAMPLE, ],
            mapping_rules=MAPPING_RULES,
            mapping=uuid.uuid4(),
        )

        self.assertEqual(Contract.objects.count(), 1)
        url = reverse('contract-detail', kwargs={'pk': contract.id})

        with mock.patch(
            'aether.ui.api.utils.kernel_data_request',
            return_value={'schemas': {'is_deleted': True}}
        ) as mock_kernel:
            response = self.client.delete(
                url,
                data={'schema': True},
                content_type='application/json',
            )
            mock_kernel.assert_called_once_with(
                url=f'mappings/{contract.mapping}/',
                method='delete',
                data={'schema': True},
                headers=wrap_kernel_headers(contract),
            )
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertIn('schemas', response_json)
        self.assertEqual(Contract.objects.count(), 0)

        contract = Contract.objects.create(
            name='Delete contract',
            pipeline=pipeline,
            entity_types=[ENTITY_SAMPLE, ],
            mapping_rules=MAPPING_RULES,
        )

        self.assertEqual(Contract.objects.count(), 1)
        url = reverse('contract-detail', kwargs={'pk': contract.id})

        with mock.patch(
            'aether.ui.api.utils.kernel_data_request',
            return_value={'schemas': {'is_deleted': True}}
        ) as mock_kernel:
            response = self.client.delete(
                url,
                content_type='application/json',
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Contract.objects.count(), 0)
        self.assertTrue(response.json()['not_published'])

        contract = Contract.objects.create(
            name='Delete contract',
            pipeline=pipeline,
            entity_types=[ENTITY_SAMPLE, ],
            mapping_rules=MAPPING_RULES,
            mapping=uuid.uuid4(),
        )
        res = Response()
        res.status_code = 404
        with mock.patch(
            'aether.ui.api.utils.kernel_data_request',
            side_effect=HTTPError('url', 404, response=res)
        ) as exp_mock_kernel:
            url = reverse('contract-detail', kwargs={'pk': contract.id})
            response = self.client.delete(
                url,
                data={'schema': True},
                content_type='application/json',
            )
            exp_mock_kernel.assert_called_once_with(
                url=f'mappings/{contract.mapping}/',
                method='delete',
                data={'schema': True},
                headers=wrap_kernel_headers(contract),
            )
            self.assertEqual(response.status_code, 204)
            self.assertEqual(Contract.objects.count(), 0)

        contract = Contract.objects.create(
            name='Delete contract',
            pipeline=pipeline,
            entity_types=[ENTITY_SAMPLE, ],
            mapping_rules=MAPPING_RULES,
            mapping=uuid.uuid4(),
        )
        with mock.patch(
            'aether.ui.api.utils.kernel_data_request',
            side_effect=Exception('Error in deleteing contract')
        ) as exp_mock_kernel:
            url = reverse('contract-detail', kwargs={'pk': contract.id})
            response = self.client.delete(
                url,
                data={'schema': True},
                content_type='application/json',
            )
            exp_mock_kernel.assert_called_once_with(
                url=f'mappings/{contract.mapping}/',
                method='delete',
                data={'schema': True},
                headers=wrap_kernel_headers(contract),
            )
            self.assertEqual(response.status_code, 500)
            self.assertEqual(Contract.objects.count(), 1)

        res.status_code = 401
        with mock.patch(
            'aether.ui.api.utils.kernel_data_request',
            side_effect=HTTPError('url', 401, response=res)
        ) as exp_mock_kernel:
            url = reverse('contract-detail', kwargs={'pk': contract.id})
            response = self.client.delete(
                url,
                data={'schema': True},
                content_type='application/json',
            )
            exp_mock_kernel.assert_called_once_with(
                url=f'mappings/{contract.mapping}/',
                method='delete',
                data={'schema': True},
                headers=wrap_kernel_headers(contract),
            )
            self.assertEqual(response.status_code, 401)
            self.assertEqual(Contract.objects.count(), 1)

    def test__published_pipeline__delete(self):
        INPUT_SAMPLE = {
            'name': 'John',
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
                    'name': 'name',
                    'type': ['null', 'string'],
                },
            ],
        }

        MAPPING_RULES = [
            {
                'source': '#!uuid',
                'destination': 'Person.id'
            },
        ]
        pipeline = Pipeline.objects.create(
            name='Delete pipeline',
            project=Project.objects.create(name='Delete project'),
            input=INPUT_SAMPLE,
            schema=ENTITY_SAMPLE,
            mappingset=uuid.uuid4(),
        )
        Contract.objects.create(
            name='Delete contract',
            pipeline=pipeline,
            entity_types=[ENTITY_SAMPLE, ],
            mapping_rules=MAPPING_RULES,
            mapping=uuid.uuid4(),
        )

        self.assertEqual(Pipeline.objects.count(), 1)
        url = reverse('pipeline-detail', kwargs={'pk': pipeline.id})

        with mock.patch(
            'aether.ui.api.utils.kernel_data_request',
            return_value={'schemas': {'is_deleted': True}}
        ) as mock_kernel:
            response = self.client.delete(
                url,
                content_type='application/json',
            )
            mock_kernel.assert_called_once_with(
                url=f'mappingsets/{pipeline.mappingset}/',
                method='delete',
                data={},
                headers=wrap_kernel_headers(pipeline),
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Pipeline.objects.count(), 0)
        self.assertEqual(Contract.objects.count(), 0)

        pipeline = Pipeline.objects.create(
            name='Delete pipeline',
            project=Project.objects.create(name='Delete project'),
            input=INPUT_SAMPLE,
            schema=ENTITY_SAMPLE,
        )
        Contract.objects.create(
            name='Delete contract',
            pipeline=pipeline,
            entity_types=[ENTITY_SAMPLE, ],
            mapping_rules=MAPPING_RULES,
            mapping=uuid.uuid4(),
        )

        self.assertEqual(Pipeline.objects.count(), 1)
        url = reverse('pipeline-detail', kwargs={'pk': pipeline.id})

        with mock.patch(
            'aether.ui.api.utils.kernel_data_request',
            return_value={'schemas': {'is_deleted': True}}
        ) as mock_kernel:
            response = self.client.delete(
                url,
                content_type='application/json',
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Pipeline.objects.count(), 0)
        self.assertEqual(Contract.objects.count(), 0)
        self.assertTrue(response.json()['not_published'])

        pipeline = Pipeline.objects.create(
            name='Delete pipeline',
            project=Project.objects.create(name='Delete project'),
            input=INPUT_SAMPLE,
            schema=ENTITY_SAMPLE,
            mappingset=uuid.uuid4(),
        )
        Contract.objects.create(
            name='Delete contract',
            pipeline=pipeline,
            entity_types=[ENTITY_SAMPLE, ],
            mapping_rules=MAPPING_RULES,
            mapping=uuid.uuid4(),
        )
        res = Response()
        res.status_code = 404
        with mock.patch(
            'aether.ui.api.utils.kernel_data_request',
            side_effect=HTTPError('url', 404, response=res)
        ) as exp_mock_kernel:
            url = reverse('pipeline-detail', kwargs={'pk': pipeline.id})
            response = self.client.delete(
                url,
                content_type='application/json',
            )
            exp_mock_kernel.assert_called_once_with(
                url=f'mappingsets/{pipeline.mappingset}/',
                method='delete',
                data={},
                headers=wrap_kernel_headers(pipeline),
            )
            self.assertEqual(response.status_code, 204)
            self.assertEqual(Contract.objects.count(), 0)
            self.assertEqual(Pipeline.objects.count(), 0)

        pipeline = Pipeline.objects.create(
            name='Delete pipeline',
            project=Project.objects.create(name='Delete project'),
            input=INPUT_SAMPLE,
            schema=ENTITY_SAMPLE,
            mappingset=uuid.uuid4(),
        )
        Contract.objects.create(
            name='Delete contract',
            pipeline=pipeline,
            entity_types=[ENTITY_SAMPLE, ],
            mapping_rules=MAPPING_RULES,
            mapping=uuid.uuid4(),
        )
        with mock.patch(
            'aether.ui.api.utils.kernel_data_request',
            side_effect=Exception('Error in deleteing pipeline')
        ) as exp_mock_kernel:
            url = reverse('pipeline-detail', kwargs={'pk': pipeline.id})
            response = self.client.delete(
                url,
                content_type='application/json',
            )
            exp_mock_kernel.assert_called_once_with(
                url=f'mappingsets/{pipeline.mappingset}/',
                method='delete',
                data={},
                headers=wrap_kernel_headers(pipeline),
            )
            self.assertEqual(response.status_code, 500)
            self.assertEqual(Contract.objects.count(), 1)
            self.assertEqual(Pipeline.objects.count(), 1)

        res.status_code = 401
        with mock.patch(
            'aether.ui.api.utils.kernel_data_request',
            side_effect=HTTPError('url', 401, response=res)
        ) as exp_mock_kernel:
            url = reverse('pipeline-detail', kwargs={'pk': pipeline.id})
            response = self.client.delete(
                url,
                content_type='application/json',
            )
            exp_mock_kernel.assert_called_once_with(
                url=f'mappingsets/{pipeline.mappingset}/',
                method='delete',
                data={},
                headers=wrap_kernel_headers(pipeline),
            )
            self.assertEqual(response.status_code, 401)
            self.assertEqual(Contract.objects.count(), 1)
            self.assertEqual(Pipeline.objects.count(), 1)
