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

from django.test import TestCase

from aether.common.kernel import utils as kernel_utils

from ..models import Pipeline, Contract


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


class MockResponse:
    def __init__(self, status_code, json_data=None, text=None):
        if json_data is None:
            json_data = {}
        self.status_code = status_code
        self.json_data = json_data
        self.content = json.dumps(json_data)
        self.text = text

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(self.status_code)

    def json(self):
        return self.json_data


class ModelsTests(TestCase):

    def setUp(self):
        # check Kernel testing server
        self.assertTrue(kernel_utils.test_connection())
        self.KERNEL_URL = kernel_utils.get_kernel_server_url() + '/validate-mappings/'
        self.KERNEL_HEADERS = kernel_utils.get_auth_header()

    def test__str(self):
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
        )
        self.assertEqual(str(pipeline), 'Pipeline test')
        contract = Contract.objects.create(
            name='Contact test',
            pipeline=pipeline
        )
        self.assertEqual(str(contract), 'Contact test')

    def test__pipeline__save__missing_requirements(self):
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
        )
        contract = Contract.objects.create(
            name='Contract test',
            pipeline=pipeline
        )

        # default
        self.assertEqual(contract.mapping_errors, [])
        self.assertEqual(contract.output, [])

        # no input
        pipeline.input = {}
        contract.mapping = [{'source': '#!uuid', 'destination': 'Person.id'}]
        contract.entity_types = [ENTITY_SAMPLE]
        pipeline.save()
        contract.save()
        self.assertEqual(contract.mapping_errors, [])
        self.assertEqual(contract.output, [])

        # no mapping rules
        pipeline.input = INPUT_SAMPLE
        contract.mapping = []
        contract.entity_types = [ENTITY_SAMPLE]
        pipeline.save()
        contract.save()
        self.assertEqual(contract.mapping_errors, [])
        self.assertEqual(contract.output, [])

        # no entity types
        pipeline.input = INPUT_SAMPLE
        contract.mapping = [{'source': '#!uuid', 'destination': 'Person.id'}]
        contract.entity_types = []
        pipeline.save()
        contract.save()
        self.assertEqual(contract.mapping_errors, [])
        self.assertEqual(contract.output, [])

    @mock.patch('aether.ui.api.utils.utils.test_connection', new=mock_return_false)
    def test__pipeline__save__test_connection_fail(self):
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
            input=INPUT_SAMPLE,
        )

        contract = Contract.objects.create(
            name='Contract test',
            pipeline=pipeline,
            entity_types=[ENTITY_SAMPLE],
            mapping=[{'source': '#!uuid', 'destination': 'Person.id'}],
        )

        self.assertEqual(
            contract.mapping_errors,
            [{'description': 'It was not possible to connect to Aether Kernel.'}]
        )
        self.assertEqual(contract.output, [])

    @mock.patch('aether.ui.api.utils.utils.test_connection', new=mock_return_true)
    @mock.patch('requests.post', return_value=MockResponse(500, text='Internal Server Error'))
    def test__pipeline__save__with_server_error(self, mock_post):
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
            input=INPUT_SAMPLE,
        )
        contract = Contract.objects.create(
            name='Contract test',
            pipeline=pipeline,
            entity_types=[ENTITY_SAMPLE],
            mapping=[{'source': '#!uuid', 'destination': 'Person.id'}],
        )
        self.assertEqual(
            contract.mapping_errors,
            [{'description': f'It was not possible to validate the pipeline: Internal Server Error'}]
        )
        self.assertEqual(contract.output, [])
        mock_post.assert_called_once()
        mock_post.assert_called_once_with(
            url=self.KERNEL_URL,
            headers=self.KERNEL_HEADERS,
            json={
                'submission_payload': INPUT_SAMPLE,
                'mapping_definition': {
                    'entities': {
                        'Person': None,
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

    @mock.patch('aether.ui.api.utils.utils.test_connection', new=mock_return_true)
    @mock.patch('requests.post',
                return_value=MockResponse(400, {
                    'entities': [],
                    'mapping_errors': ['test']
                }))
    def test__pipeline__save__with_bad_request(self, mock_post):
        malformed_schema = {'name': 'Person'}
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
            input=INPUT_SAMPLE,
        )
        contract = Contract.objects.create(
            entity_types=[malformed_schema],
            mapping=[{'source': '#!uuid', 'destination': 'Person.id'}],
            pipeline=pipeline
        )
        self.assertEqual(
            contract.mapping_errors,
            [{'description': 'test'}]
        )
        self.assertEqual(contract.output, [])
        mock_post.assert_called_once()
        mock_post.assert_called_once_with(
            url=self.KERNEL_URL,
            headers=self.KERNEL_HEADERS,
            json={
                'submission_payload': INPUT_SAMPLE,
                'mapping_definition': {
                    'entities': {
                        'Person': None,
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

    @mock.patch('aether.ui.api.utils.utils.test_connection', new=mock_return_true)
    @mock.patch('requests.post',
                return_value=MockResponse(200, {
                    'entities_2': 'something',
                    'mapping_errors_2': 'something else',
                }))
    def test__pipeline__save__with_wrong_response(self, mock_post):
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
            input=INPUT_SAMPLE,
        )
        contract = Contract.objects.create(
            entity_types=[ENTITY_SAMPLE],
            mapping=[{'source': '#!uuid', 'destination': 'Person.id'}],
            pipeline=pipeline
        )
        self.assertEqual(contract.mapping_errors, [])
        self.assertEqual(contract.output, [])
        mock_post.assert_called_once()
        mock_post.assert_called_once_with(
            url=self.KERNEL_URL,
            headers=self.KERNEL_HEADERS,
            json={
                'submission_payload': INPUT_SAMPLE,
                'mapping_definition': {
                    'entities': {
                        'Person': None,
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

    @mock.patch('aether.ui.api.utils.utils.test_connection', new=mock_return_true)
    @mock.patch('requests.post',
                return_value=MockResponse(200, {
                    'entities': 'something',
                    'mapping_errors': 'something else',
                }))
    def test__pipeline__save__validated(self, mock_post):
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
            input=INPUT_SAMPLE,
        )
        contract = Contract.objects.create(
            entity_types=[ENTITY_SAMPLE],
            mapping=[
                {'source': '#!uuid', 'destination': 'Person.id'},
                {'source': '$.firstName', 'destination': 'Person.firstName'},
            ],
            pipeline=pipeline
        )

        self.assertEqual(contract.mapping_errors, 'something else')
        self.assertEqual(contract.output, 'something')
        mock_post.assert_called_once()
        mock_post.assert_called_once_with(
            url=self.KERNEL_URL,
            headers=self.KERNEL_HEADERS,
            json={
                'submission_payload': INPUT_SAMPLE,
                'mapping_definition': {
                    'entities': {
                        'Person': None,
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

    def test__pipeline_workflow__with_kernel__wrong_rules(self):
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
            input=INPUT_SAMPLE,
        )
        contract = Contract.objects.create(
            entity_types=[ENTITY_SAMPLE],
            mapping=[
                {'source': '#!uuid', 'destination': 'Person.id'},
                {'source': '$.not_a_real_key', 'destination': 'Person.firstName'},
            ],
            pipeline=pipeline
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

    def test__pipeline_workflow__with_kernel__missing_id(self):
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
            input=INPUT_SAMPLE,
        )
        contract = Contract.objects.create(
            entity_types=[ENTITY_SAMPLE],
            mapping=[{'source': '$.surname', 'destination': 'Person.firstName'}],
            pipeline=pipeline
        )

        # error when there is no id rule for the entity
        self.assertIn(
            'is not a valid uuid',
            contract.mapping_errors[0]['description'],
        )
        self.assertNotIn('path', contract.mapping_errors[0])
        self.assertEqual(contract.output, [])

    def test__pipeline_workflow__with_kernel__no_errors(self):
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
            input=INPUT_SAMPLE,
        )
        contract = Contract.objects.create(
            entity_types=[ENTITY_SAMPLE],
            mapping=[
                {'source': '#!uuid', 'destination': 'Person.id'},
                {'source': '$.surname', 'destination': 'Person.firstName'},
            ],
            pipeline=pipeline
        )

        self.assertEqual(contract.mapping_errors, [])
        self.assertNotEqual(contract.output, [])
        self.assertIsNotNone(contract.output[0]['id'], 'Generated id!')
        self.assertEqual(contract.output[0]['firstName'], 'Smith')
