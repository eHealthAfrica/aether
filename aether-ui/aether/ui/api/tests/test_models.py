# Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
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

from django.conf import settings
from django.test import TestCase, override_settings
from aether.sdk.unittest import MockResponse

from ..kernel_utils import (
    check_kernel_connection,
    get_kernel_url,
    get_kernel_auth_header,
)
from ..models import Project, Pipeline, Contract


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


def mock_return_false(*args):
    return False


def mock_return_true(*args):
    return True


@override_settings(MULTITENANCY=False)
class ModelsTests(TestCase):

    def setUp(self):
        super(ModelsTests, self).setUp()

        # check Kernel testing server
        self.assertTrue(check_kernel_connection())
        self.KERNEL_URL = get_kernel_url() + '/validate-mappings/'
        self.KERNEL_HEADERS = get_kernel_auth_header()

    def test__models(self):
        project = Project.objects.create(name='Project test')
        self.assertEqual(str(project), 'Project test')
        self.assertFalse(project.is_accessible(settings.DEFAULT_REALM))
        self.assertIsNone(project.get_realm())

        pipeline = Pipeline.objects.create(
            name='Pipeline test',
            project=project,
            input=INPUT_SAMPLE,
        )
        self.assertEqual(str(pipeline), 'Pipeline test')
        self.assertIsNotNone(pipeline.input_prettified)
        self.assertIsNotNone(pipeline.schema_prettified)
        self.assertFalse(pipeline.is_accessible(settings.DEFAULT_REALM))
        self.assertIsNone(pipeline.get_realm())

        contract = Contract.objects.create(
            name='Contract test',
            pipeline=pipeline,
            mapping_rules=[{'source': '#!uuid', 'destination': 'Person.id'}],
        )
        self.assertEqual(str(contract), 'Contract test')
        self.assertIsNotNone(contract.entity_types_prettified)
        self.assertIsNotNone(contract.mapping_rules_prettified)
        self.assertIsNotNone(contract.mapping_errors_prettified)
        self.assertIsNotNone(contract.output_errors_prettified)
        self.assertIsNotNone(contract.kernel_refs_errors_prettified)
        self.assertEqual(contract.kernel_rules, [['#!uuid', 'Person.id']])
        self.assertFalse(contract.is_accessible(settings.DEFAULT_REALM))
        self.assertIsNone(contract.get_realm())

    def test__pipeline__and__contract__save__missing_requirements(self):
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
            project=Project.objects.create(name='Project test'),
        )
        contract = Contract.objects.create(
            name='Contract test',
            pipeline=pipeline,
        )

        # default
        self.assertEqual(contract.mapping_errors, [])
        self.assertEqual(contract.output, [])

        # no input
        pipeline.input = {}
        pipeline.save()
        contract.mapping_rules = [{'source': '#!uuid', 'destination': 'Person.id'}]
        contract.entity_types = [ENTITY_SAMPLE]
        contract.save()
        self.assertEqual(contract.mapping_errors, [])
        self.assertEqual(contract.output, [])

        # no mapping rules
        pipeline.input = INPUT_SAMPLE
        pipeline.save()
        contract.mapping_rules = []
        contract.entity_types = [ENTITY_SAMPLE]
        contract.save()
        self.assertEqual(contract.mapping_errors, [])
        self.assertEqual(contract.output, [])

        # no entity types
        pipeline.input = INPUT_SAMPLE
        pipeline.save()
        contract.mapping_rules = [{'source': '#!uuid', 'destination': 'Person.id'}]
        contract.entity_types = []
        contract.save()
        self.assertEqual(contract.mapping_errors, [])
        self.assertEqual(contract.output, [])

    @mock.patch('aether.ui.api.utils.kernel_utils.check_kernel_connection', new=mock_return_false)
    def test__contract__save__test_connection_fail(self):
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
            input=INPUT_SAMPLE,
            project=Project.objects.create(name='Project test'),
        )

        contract = Contract.objects.create(
            name='Contract test',
            pipeline=pipeline,
            entity_types=[ENTITY_SAMPLE],
            mapping_rules=[{'source': '#!uuid', 'destination': 'Person.id'}],
        )

        self.assertEqual(
            contract.mapping_errors,
            [{'description': 'It was not possible to connect to Aether Kernel.'}]
        )
        self.assertEqual(contract.output, [])

    @mock.patch('aether.ui.api.utils.kernel_utils.check_kernel_connection', new=mock_return_true)
    @mock.patch('aether.ui.api.utils.request',
                return_value=MockResponse(500, text='Internal Server Error'))
    def test__contract__save__with_server_error(self, mock_post):
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
            input=INPUT_SAMPLE,
            project=Project.objects.create(name='Project test'),
        )
        contract = Contract.objects.create(
            name='Contract test',
            pipeline=pipeline,
            entity_types=[ENTITY_SAMPLE],
            mapping_rules=[{'source': '#!uuid', 'destination': 'Person.id'}],
        )
        self.assertEqual(
            contract.mapping_errors,
            [{'description': f'It was not possible to validate the contract: Internal Server Error'}]
        )
        self.assertEqual(contract.output, [])
        mock_post.assert_called_once()
        mock_post.assert_called_once_with(
            method='post',
            url=self.KERNEL_URL,
            headers=self.KERNEL_HEADERS,
            json={
                'submission_payload': INPUT_SAMPLE,
                'mapping_definition': {
                    'entities': {
                        'Person': mock.ANY,
                    },
                    'mapping': [
                        ['#!uuid', 'Person.id'],
                    ],
                },
                'schemas': {
                    'Person': ENTITY_SAMPLE,
                },
            },
        )

    @mock.patch('aether.ui.api.utils.kernel_utils.check_kernel_connection', new=mock_return_true)
    @mock.patch('aether.ui.api.utils.request',
                return_value=MockResponse(400, {
                    'entities': [],
                    'mapping_errors': ['test']
                }))
    def test__contract__save__with_bad_request(self, mock_post):
        malformed_schema = {'name': 'Person'}
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
            input=INPUT_SAMPLE,
            project=Project.objects.create(name='Project test'),
        )
        contract = Contract.objects.create(
            entity_types=[malformed_schema],
            mapping_rules=[{'source': '#!uuid', 'destination': 'Person.id'}],
            pipeline=pipeline,
        )
        self.assertEqual(
            contract.mapping_errors,
            [{'description': 'test'}]
        )
        self.assertEqual(contract.output, [])
        mock_post.assert_called_once()
        mock_post.assert_called_once_with(
            method='post',
            url=self.KERNEL_URL,
            headers=self.KERNEL_HEADERS,
            json={
                'submission_payload': INPUT_SAMPLE,
                'mapping_definition': {
                    'entities': {
                        'Person': mock.ANY,
                    },
                    'mapping': [
                        ['#!uuid', 'Person.id'],
                    ],
                },
                'schemas': {
                    'Person': malformed_schema,
                },
            },
        )

    @mock.patch('aether.ui.api.utils.kernel_utils.check_kernel_connection', new=mock_return_true)
    @mock.patch('aether.ui.api.utils.request',
                return_value=MockResponse(200, {
                    'entities_2': 'something',
                    'mapping_errors_2': 'something else',
                }))
    def test__contract__save__with_wrong_response(self, mock_post):
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
            input=INPUT_SAMPLE,
            project=Project.objects.create(name='Project test'),
        )
        contract = Contract.objects.create(
            entity_types=[ENTITY_SAMPLE],
            mapping_rules=[{'source': '#!uuid', 'destination': 'Person.id'}],
            pipeline=pipeline,
        )
        self.assertEqual(contract.mapping_errors, [])
        self.assertEqual(contract.output, [])
        mock_post.assert_called_once()
        mock_post.assert_called_once_with(
            method='post',
            url=self.KERNEL_URL,
            headers=self.KERNEL_HEADERS,
            json={
                'submission_payload': INPUT_SAMPLE,
                'mapping_definition': {
                    'entities': {
                        'Person': mock.ANY,
                    },
                    'mapping': [
                        ['#!uuid', 'Person.id'],
                    ],
                },
                'schemas': {
                    'Person': ENTITY_SAMPLE,
                },
            },
        )

    @mock.patch('aether.ui.api.utils.kernel_utils.check_kernel_connection', new=mock_return_true)
    @mock.patch('aether.ui.api.utils.request',
                return_value=MockResponse(200, {
                    'entities': 'something',
                    'mapping_errors': 'something else',
                }))
    def test__contract__save__validated(self, mock_post):
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
            input=INPUT_SAMPLE,
            project=Project.objects.create(name='Project test'),
        )
        contract = Contract.objects.create(
            entity_types=[ENTITY_SAMPLE],
            mapping_rules=[
                {'source': '#!uuid', 'destination': 'Person.id'},
                {'source': '$.firstName', 'destination': 'Person.firstName'},
            ],
            pipeline=pipeline,
        )

        self.assertEqual(contract.mapping_errors, 'something else')
        self.assertEqual(contract.output, 'something')
        mock_post.assert_called_once()
        mock_post.assert_called_once_with(
            method='post',
            url=self.KERNEL_URL,
            headers=self.KERNEL_HEADERS,
            json={
                'submission_payload': INPUT_SAMPLE,
                'mapping_definition': {
                    'entities': {
                        'Person': mock.ANY,
                    },
                    'mapping': [
                        ['#!uuid', 'Person.id'],
                        ['$.firstName', 'Person.firstName'],
                    ],
                },
                'schemas': {
                    'Person': ENTITY_SAMPLE,
                },
            },
        )

    def test__pipeline__and__contract__workflow__with_kernel__wrong_rules(self):
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
            input=INPUT_SAMPLE,
            project=Project.objects.create(name='Project test'),
        )
        contract = Contract.objects.create(
            entity_types=[ENTITY_SAMPLE],
            mapping_rules=[
                {'source': '#!uuid', 'destination': 'Person.id'},
                {'source': '$.not_a_real_key', 'destination': 'Person.firstName'},
            ],
            pipeline=pipeline,
        )

        self.assertEqual(contract.output, [], 'No output if there are errors')
        self.assertEqual(contract.mapping_errors[0],
                         {'path': '$.not_a_real_key', 'description': 'No match for path'})

        # the last entry is the extracted entity
        self.assertIn(
            'Expected type "string" at path "Person.firstName"',
            contract.mapping_errors[1]['description'],
        )
        expected_errors = [
            'No match for path',
            'Expected type "string" at path "Person.firstName"',
        ]
        for expected, result in zip(expected_errors, contract.mapping_errors):
            self.assertIn(expected, result['description'])

    def test__pipeline__and__contract__workflow__with_kernel__missing_id(self):
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
            input=INPUT_SAMPLE,
            project=Project.objects.create(name='Project test'),
        )
        contract = Contract.objects.create(
            entity_types=[ENTITY_SAMPLE],
            mapping_rules=[{'source': '$.surname', 'destination': 'Person.firstName'}],
            pipeline=pipeline,
        )

        # error when there is no id rule for the entity
        self.assertIn(
            'is not a valid uuid',
            contract.mapping_errors[0]['description'],
        )
        self.assertNotIn('path', contract.mapping_errors[0])
        self.assertEqual(contract.output, [])

    def test__pipeline__and__contract__workflow__with_kernel__success(self):
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
            input=INPUT_SAMPLE,
            project=Project.objects.create(name='Project test'),
        )
        contract = Contract.objects.create(
            entity_types=[ENTITY_SAMPLE],
            mapping_rules=[
                {'source': '#!uuid', 'destination': 'Person.id'},
                {'source': '$.surname', 'destination': 'Person.firstName'},
            ],
            pipeline=pipeline,
        )

        self.assertEqual(contract.mapping_errors, [])
        self.assertNotEqual(contract.output, [])
        self.assertIsNotNone(contract.output[0]['id'], 'Generated id!')
        self.assertEqual(contract.output[0]['firstName'], 'Smith')
