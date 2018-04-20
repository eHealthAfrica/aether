import mock

from django.conf import settings
from django.test import TestCase

from ..models import Pipeline

KERNEL_URL = settings.AETHER_APPS['kernel']['url'] + '/validate-mappings/'
KERNEL_HEADER = {'Authorization': 'Token ' + settings.AETHER_APPS['kernel']['token']}

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
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(self.status_code)

    def json(self):
        return self.json_data


class ModelsPipelineTests(TestCase):

    def test__str(self):
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
        )
        self.assertEqual(str(pipeline), 'Pipeline test')

    def test__pipeline__save__missing_requirements(self):
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
        )

        # default
        self.assertEqual(pipeline.mapping_errors, [])
        self.assertEqual(pipeline.output, [])

        # no input
        pipeline.input = {}
        pipeline.mapping = [{'source': '#!uuid', 'destination': 'Person.id'}]
        pipeline.entity_types = [ENTITY_SAMPLE]
        pipeline.save()
        self.assertEqual(pipeline.mapping_errors, [])
        self.assertEqual(pipeline.output, [])

        # no mapping rules
        pipeline.input = INPUT_SAMPLE
        pipeline.mapping = []
        pipeline.entity_types = [ENTITY_SAMPLE]
        pipeline.save()
        self.assertEqual(pipeline.mapping_errors, [])
        self.assertEqual(pipeline.output, [])

        # no entity types
        pipeline.input = INPUT_SAMPLE
        pipeline.mapping = [{'source': '#!uuid', 'destination': 'Person.id'}]
        pipeline.entity_types = []
        pipeline.save()
        self.assertEqual(pipeline.mapping_errors, [])
        self.assertEqual(pipeline.output, [])

    @mock.patch('aether.ui.api.utils.utils.test_connection', new=mock_return_false)
    def test__pipeline__save__test_connection_fail(self):
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
            input=INPUT_SAMPLE,
            entity_types=[ENTITY_SAMPLE],
            mapping=[{'source': '#!uuid', 'destination': 'Person.id'}],
        )

        self.assertEqual(
            pipeline.mapping_errors,
            [{'error_message': 'It was not possible to connect to Aether Kernel Server.'}]
        )
        self.assertEqual(pipeline.output, [])

    @mock.patch('aether.ui.api.utils.utils.test_connection', new=mock_return_true)
    @mock.patch('requests.post', return_value=MockResponse({}, 500))
    def test__pipeline__save__with_server_error(self, mock_post):
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
            input=INPUT_SAMPLE,
            entity_types=[ENTITY_SAMPLE],
            mapping=[{'source': '#!uuid', 'destination': 'Person.id'}],
        )
        self.assertEqual(
            pipeline.mapping_errors,
            [{'error_message': f'It was not possible to validate the pipeline: 500'}]
        )
        self.assertEqual(pipeline.output, [])
        mock_post.assert_called_once()
        mock_post.assert_called_once_with(
            url=KERNEL_URL,
            headers=KERNEL_HEADER,
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
                return_value=MockResponse({
                    'entities_2': 'something',
                    'mapping_errors_2': 'something else',
                }, 200))
    def test__pipeline__save__with_wrong_response(self, mock_post):
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
            input=INPUT_SAMPLE,
            entity_types=[ENTITY_SAMPLE],
            mapping=[{'source': '#!uuid', 'destination': 'Person.id'}],
        )
        self.assertEqual(pipeline.mapping_errors, [])
        self.assertEqual(pipeline.output, [])
        mock_post.assert_called_once()
        mock_post.assert_called_once_with(
            url=KERNEL_URL,
            headers=KERNEL_HEADER,
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
                return_value=MockResponse({
                    'entities': 'something',
                    'mapping_errors': 'something else',
                }, 200))
    def test__pipeline__save__validated(self, mock_post):
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
            input=INPUT_SAMPLE,
            entity_types=[ENTITY_SAMPLE],
            mapping=[
                {'source': '#!uuid', 'destination': 'Person.id'},
                {'source': '$.firstName', 'destination': 'Person.firstName'},
            ],
        )

        self.assertEqual(pipeline.mapping_errors, 'something else')
        self.assertEqual(pipeline.output, 'something')
        mock_post.assert_called_once()
        mock_post.assert_called_once_with(
            url=KERNEL_URL,
            headers=KERNEL_HEADER,
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

    def test__pipeline_workflow__with_kernel(self):
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
            input=INPUT_SAMPLE,
            entity_types=[ENTITY_SAMPLE],
            mapping=[],
        )

        pipeline.mapping = [
            {'source': '#!uuid', 'destination': 'Person.id'},
            {'source': '$.not_a_real_key', 'destination': 'Person.firstName'},
        ]
        pipeline.save()
        self.assertEqual(pipeline.mapping_errors, [
            {'path': '$.not_a_real_key', 'error_message': 'No match for path'}
        ])
        self.assertIsNotNone(pipeline.output[0]['id'], 'Generated id!')
        self.assertIsNone(pipeline.output[0]['firstName'],
                          'Wrong jsonpaths return None values')

        pipeline.mapping = [
            {'source': '#!uuid', 'destination': 'Person.id'},
            {'source': '$.surname', 'destination': 'Person.firstName'},
        ]
        pipeline.save()
        self.assertEqual(pipeline.mapping_errors, [])
        self.assertNotEqual(pipeline.output, [])
        self.assertIsNotNone(pipeline.output[0]['id'], 'Generated id!')
        self.assertEqual(pipeline.output[0]['firstName'], 'Smith')

    def test__pipeline_workflow__with_kernel__missing_id(self):
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
            input=INPUT_SAMPLE,
            entity_types=[ENTITY_SAMPLE],
            mapping=[{'source': '$.surname', 'destination': 'Person.firstName'}],
        )

        # weird error when there is no id rule for the entity
        self.assertEqual(
            pipeline.mapping_errors[0]['error_message'],
            'It was not possible to validate the pipeline: '
            '400 Client Error: Bad Request '
            f'for url: {KERNEL_URL}'
        )
        self.assertEqual(pipeline.output, [])
