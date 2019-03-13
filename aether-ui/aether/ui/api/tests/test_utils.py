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
import mock

from django.conf import settings
from django.test import TestCase

from ..models import Project, Pipeline, Contract
from .. import utils


class UtilsTest(TestCase):

    def setUp(self):
        super(UtilsTest, self).setUp()

        self.KERNEL_ID = str(uuid.uuid4())

        Project.objects.all().delete()

    def tearDown(self):
        self.helper__delete_in_kernel('projects', self.KERNEL_ID)
        self.helper__delete_in_kernel('schemas', self.KERNEL_ID)

        super(UtilsTest, self).tearDown()

    def helper__kernel_data(self, *args, **kwargs):
        try:
            return utils.kernel_data_request(*args, **kwargs)
        except Exception:
            pass  # ignore

    def helper__delete_in_kernel(self, model, pk):
        self.helper__kernel_data(f'{model}/{pk}/', 'delete')

    def test_get_default_project(self):
        self.assertEqual(Project.objects.count(), 0)

        # creates a project
        project = utils.get_default_project()
        self.assertEqual(project.name, settings.DEFAULT_PROJECT_NAME)
        self.assertTrue(project.is_default)
        self.assertEqual(Project.objects.count(), 1)

        # call it a second time does not create a new one
        project_2 = utils.get_default_project()
        self.assertEqual(project.pk, project_2.pk)
        self.assertEqual(Project.objects.count(), 1)

    def test_kernel_data_request(self):
        result = utils.kernel_data_request('projects/')
        self.assertIn('count', result)

        with self.assertRaises(Exception):
            utils.kernel_data_request('projectss', 'post', {'wrong-input': 'tests'})

    def test_publish(self):
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

        contract = Contract.objects.create(
            name='Publishing contract',
            pipeline=Pipeline.objects.create(
                name='Publishing pipeline',
                project=Project.objects.create(
                    name='Publishing project',
                ),
                input=INPUT_SAMPLE,
                schema=ENTITY_SAMPLE,
            ),
            entity_types=[ENTITY_SAMPLE],
            mapping_rules=MAPPING_RULES,
        )

        pipeline = contract.pipeline
        project = pipeline.project
        project_id = str(project.pk)

        # publish with exceptions
        with self.assertRaises(utils.PublishError) as pe:
            with mock.patch('aether.ui.api.utils.kernel_data_request',
                            side_effect=Exception('Error in project')) as mock_kernel:
                utils.publish_project(project)
                mock_kernel.assert_called_once_with(
                    url=f'projects/{project_id}/artefacts/',
                    method='patch',
                    data=mock.ANY,
                    headers={'Authorization': mock.ANY},
                )
            self.assertIn('Error in project', str(pe.exception))

        with self.assertRaises(utils.PublishError) as pe:
            with mock.patch('aether.ui.api.utils.kernel_data_request',
                            side_effect=Exception('Error in pipeline')) as mock_kernel:
                utils.publish_pipeline(pipeline)
                mock_kernel.assert_called_once_with(
                    url=f'projects/{project_id}/artefacts/',
                    method='patch',
                    data=mock.ANY,
                    headers={'Authorization': mock.ANY},
                )
            self.assertIn('Error in pipeline', str(pe.exception))

        with self.assertRaises(utils.PublishError) as pe:
            with mock.patch('aether.ui.api.utils.kernel_data_request',
                            side_effect=Exception('Error in contract')) as mock_kernel:
                with mock.patch('aether.ui.api.utils.publish_preflight',
                                return_value={}) as mock_preflight:
                    utils.publish_contract(contract)
                    mock_preflight.assert_called_once()
                    mock_kernel.assert_called_once_with(
                        url=f'projects/{project_id}/artefacts/',
                        method='patch',
                        data=mock.ANY,
                        headers={'Authorization': mock.ANY},
                    )
            self.assertIn('Error in contract', str(pe.exception))

        # publish without exceptions
        with mock.patch('aether.ui.api.utils.kernel_data_request') as mock_kernel:
            utils.publish_project(project)
            mock_kernel.assert_called_once_with(
                url=f'projects/{project_id}/artefacts/',
                method='patch',
                data={'name': 'Publishing project'},
            )

        contract.is_read_only = True
        contract.save()

        with mock.patch('aether.ui.api.utils.kernel_data_request') as mock_kernel:
            utils.publish_pipeline(pipeline)
            mock_kernel.assert_called_once_with(
                url=f'projects/{project_id}/artefacts/',
                method='patch',
                data={
                    'action': 'create',  # contract is read only
                    'name': 'Publishing project',
                    'mappingsets': [{
                        'id': mock.ANY,
                        'name': 'Publishing pipeline',
                        'input': INPUT_SAMPLE,
                        'schema': ENTITY_SAMPLE,
                    }]
                },
            )

        contract.is_read_only = False
        contract.save()

        with mock.patch('aether.ui.api.utils.kernel_data_request') as mock_kernel:
            utils.publish_pipeline(pipeline)
            mock_kernel.assert_called_once_with(
                url=f'projects/{project_id}/artefacts/',
                method='patch',
                data={
                    'action': 'upsert',  # no read only contracts
                    'name': 'Publishing project',
                    'mappingsets': [{
                        'id': mock.ANY,
                        'name': 'Publishing pipeline',
                        'input': INPUT_SAMPLE,
                        'schema': ENTITY_SAMPLE,
                    }]
                },
            )

        with mock.patch('aether.ui.api.utils.kernel_data_request') as mock_kernel:
            with mock.patch('aether.ui.api.utils.publish_preflight',
                            return_value={}) as mock_preflight:
                utils.publish_contract(contract)
                mock_preflight.assert_called_once()
                mock_kernel.assert_called_once_with(
                    url=f'projects/{project_id}/artefacts/',
                    method='patch',
                    data={
                        'name': 'Publishing project',
                        'mappingsets': [{
                            'id': mock.ANY,
                            'name': 'Publishing pipeline',
                            'input': INPUT_SAMPLE,
                            'schema': ENTITY_SAMPLE,
                        }],
                        'schemas': [{
                            'id': mock.ANY,
                            'name': 'Person',
                            'definition': ENTITY_SAMPLE,
                        }],
                        'mappings': [{
                            'id': mock.ANY,
                            'name': 'Publishing contract',
                            'definition': {
                                'mapping': [['#!uuid', 'Person.id']],
                                'entities': {'Person': mock.ANY},
                            },
                            'mappingset': mock.ANY,
                            'is_active': True,
                            'is_ready_only': False,
                        }],
                    },
                )

    def test__kernel_workflow(self):
        # create a project in kernel and bring it to ui
        url = f'projects/{self.KERNEL_ID}/avro-schemas/'
        artefacts = {
            'name': 'Kernel Project',
            'avro_schemas': [
                {
                    'id': self.KERNEL_ID,
                    'definition': {
                        'name': 'Person',
                        'type': 'record',
                        'fields': [
                            {
                                'name': 'id',
                                'type': 'string',
                            },
                        ],
                    },
                },
            ],
        }
        self.helper__kernel_data(url=url, method='patch', data=artefacts)
        # fetch its artefacts and check
        res = self.helper__kernel_data(url=f'projects/{self.KERNEL_ID}/artefacts/')
        self.assertEqual(
            res,
            {
                'project': self.KERNEL_ID,
                'schemas': [self.KERNEL_ID],
                'project_schemas': [self.KERNEL_ID],
                'mappingsets': [self.KERNEL_ID],
                'mappings': [self.KERNEL_ID],
            }
        )

        self.assertFalse(Project.objects.filter(pk=self.KERNEL_ID).exists())

        # bring them to ui
        utils.kernel_artefacts_to_ui_artefacts()

        self.assertTrue(Project.objects.filter(pk=self.KERNEL_ID).exists())
        project = Project.objects.get(pk=self.KERNEL_ID)

        self.assertIn('Kernel Project', project.name)
        self.assertEqual(project.pipelines.count(), 1)
        self.assertEqual(project.pipelines.first().contracts.count(), 1)
        contract = project.pipelines.first().contracts.first()
        self.assertEqual(
            contract.kernel_refs,
            {
                'entities': {'Person': self.KERNEL_ID},
                'schemas': {'Person': self.KERNEL_ID},
            }
        )

        # bring them again to ui
        utils.kernel_artefacts_to_ui_artefacts()
        project.refresh_from_db()

        # nothing new
        self.assertEqual(project.pipelines.count(), 1)
        pipeline = project.pipelines.first()
        self.assertEqual(pipeline.contracts.count(), 1)

        # check publish preflight
        outcome = utils.publish_preflight(contract)
        self.assertEqual(
            outcome,
            {
                'error': ['Contract is read only'],
                'warning': [
                    'Project is already published',
                    'Pipeline (as mapping set) is already published',
                    'Contract (as mapping) is already published',
                    'Entity type "Person" (as schema) is already published',
                    'Entity type "Person" (as project schema) is already published',
                ],
                'info': [],
            }
        )

        # delete the kernel instances
        self.helper__delete_in_kernel('projects', self.KERNEL_ID)
        self.helper__delete_in_kernel('schemas', self.KERNEL_ID)

        # check that nothing is there
        res = self.helper__kernel_data(url=f'projects?id={self.KERNEL_ID}')
        self.assertEqual(res['count'], 0)
        res = self.helper__kernel_data(url=f'schemas?id={self.KERNEL_ID}')
        self.assertEqual(res['count'], 0)

        # check publish preflight again
        outcome = utils.publish_preflight(contract)
        self.assertEqual(
            outcome,
            {
                'error': ['Contract is read only'],
                'warning': [],
                'info': [
                    'Project will be published',
                    'Pipeline (as mapping set) will be published',
                    'Contract (as mapping) will be published',
                    'Entity type "Person" (as schema) will be published',
                    'Entity type "Person" (as project schema) will be published',
                ],
            }
        )

        contract.refresh_from_db()
        with self.assertRaises(utils.PublishError) as pe:
            utils.publish_contract(contract)
        self.assertIn('Contract is read only', str(pe.exception))

        contract.is_read_only = False
        contract.save()

        # check publish preflight again
        outcome = utils.publish_preflight(contract)
        self.assertEqual(
            outcome,
            {
                'error': [],
                'warning': [],
                'info': [
                    'Project will be published',
                    'Pipeline (as mapping set) will be published',
                    'Contract (as mapping) will be published',
                    'Entity type "Person" (as schema) will be published',
                    'Entity type "Person" (as project schema) will be published',
                ],
            }
        )

        res = utils.publish_contract(contract)
        self.assertEqual(
            res['artefacts'],
            {
                'project': self.KERNEL_ID,
                'mappingset': self.KERNEL_ID,
                'mapping': self.KERNEL_ID,
                'entities': {'Person': self.KERNEL_ID},
                'schemas': {'Person': self.KERNEL_ID},
            }
        )

        # check that the project is back in kernel
        res = self.helper__kernel_data(url=f'projects?id={self.KERNEL_ID}')
        self.assertEqual(res['count'], 1)

        # bring its artefacts and compare
        res = self.helper__kernel_data(url=f'projects/{self.KERNEL_ID}/artefacts/')
        self.assertEqual(
            res,
            {
                'project': self.KERNEL_ID,
                'schemas': [self.KERNEL_ID],
                'project_schemas': [self.KERNEL_ID],
                'mappingsets': [self.KERNEL_ID],
                'mappings': [self.KERNEL_ID],
            }
        )

        # break everything: change linked UUID in all artefacts
        NEW_KERNEL_ID = str(uuid.uuid4())
        new_project = Project.objects.create(pk=NEW_KERNEL_ID, name='Second')
        contract.pipeline.project = new_project     # project error
        contract.pipeline.input = {}                # not input error & input changed
        contract.pipeline.schema = {}               # schema changed
        contract.pipeline.save()
        contract.mapping_rules[0]['source'] = '$'   # rules changed
        contract.entity_types = [                   # entity type schema changed
            {
                'name': 'Person',
                'type': 'record',
                'fields': [
                    {'name': 'id', 'type': 'string'}
                ]
            }
        ]
        contract.kernel_refs = {
            'entities': {'Person': NEW_KERNEL_ID},
            'schemas': {'Person': self.KERNEL_ID},
        }
        contract.save()
        contract.refresh_from_db()

        # check publish preflight again
        outcome = utils.publish_preflight(contract)
        self.assertEqual(
            outcome,
            {
                'error': [
                    'Pipeline has no input',
                    'Pipeline belongs to a different project in kernel',
                    'Contract belongs to a different project in kernel',
                ],
                'warning': [
                    'Pipeline (as mapping set) is already published',
                    'Contract (as mapping) is already published',
                    'Entity type "Person" (as schema) is already published',
                ],
                'info': [
                    'Project will be published',
                    'Input data will be changed',
                    'Schema data will be changed',
                    'Mapping rules data will be changed',
                    'Entity type "Person" (as schema) data will be changed',
                    'Entity type "Person" (as project schema) will be published',
                ],
            }
        )

        contract.pipeline.input = {'name': 'doe'}     # rules error
        contract.pipeline.mappingset = NEW_KERNEL_ID  # pipeline wrong
        contract.pipeline.save()
        contract.mapping_rules += [                   # rules changed (length cause)
            {'source': '$', 'destination': 'Person.id'},
        ]
        contract.kernel_refs = {
            'entities': {'Person': self.KERNEL_ID},
            'schemas': {'Person': NEW_KERNEL_ID},     # project error
        }
        contract.save()
        contract.refresh_from_db()

        # check publish preflight again
        outcome = utils.publish_preflight(contract)
        self.assertEqual(
            outcome,
            {
                'error': [
                    'Contract belongs to a different project in kernel',
                    'Contract belongs to a different pipeline (mapping set) in kernel',
                    'Entity type "Person" (as project schema) belongs to a different project in kernel',
                ],
                'warning': [
                    'Contract mapping rules have errors',
                    'Contract (as mapping) is already published',
                    'Entity type "Person" (as project schema) is already published',
                ],
                'info': [
                    'Project will be published',
                    'Pipeline (as mapping set) will be published',
                    'Mapping rules data will be changed',
                    'Entity type "Person" (as schema) will be published',
                ],
            }
        )

        # cannot check schemas or project schemas
        contract.kernel_refs = {
            'entities': {},
            'schemas': {},
        }
        contract.save()
        contract.refresh_from_db()

        # check publish preflight again
        outcome = utils.publish_preflight(contract)
        self.assertEqual(
            outcome,
            {
                'error': [
                    'Contract belongs to a different project in kernel',
                    'Contract belongs to a different pipeline (mapping set) in kernel',
                ],
                'warning': [
                    'Contract mapping rules have errors',
                    'Contract (as mapping) is already published',
                ],
                'info': [
                    'Project will be published',
                    'Pipeline (as mapping set) will be published',
                    'Mapping rules data will be changed',
                    'Entity type "Person" (as schema) will be published',
                    'Entity type "Person" (as project schema) will be published',
                ],
            }
        )
