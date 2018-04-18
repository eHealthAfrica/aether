import mock

from django.test import TestCase

from ..models import Pipeline, EntityType

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

        entity_type = EntityType.objects.create(
            pipeline=pipeline,
            name='Person',
            payload=ENTITY_SAMPLE,
        )
        self.assertEqual(str(entity_type), 'Person')

    def test__pipeline__save__missing_requirements(self):
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
        )

        # no input
        self.assertEqual(pipeline.mapping_errors, [])
        self.assertEqual(pipeline.output, [])

        # no mapping rules
        pipeline.input = INPUT_SAMPLE
        pipeline.save()
        self.assertEqual(pipeline.mapping_errors, [])
        self.assertEqual(pipeline.output, [])

        # no entity types
        pipeline.mapping = [['#!uuid', 'Person.id']]
        pipeline.save()
        self.assertEqual(pipeline.mapping_errors, [])
        self.assertEqual(pipeline.output, [])

    @mock.patch('aether.ui.api.utils.utils.test_connection', new=mock_return_false)
    def test__pipeline__save__test_connection_fail(self):
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
            input=INPUT_SAMPLE,
        )
        EntityType.objects.create(
            pipeline=pipeline,
            name='Person',
            payload=ENTITY_SAMPLE,
        )

        # no mapping rules
        self.assertEqual(pipeline.mapping_errors, [])
        self.assertEqual(pipeline.output, [])

        # first mapping rule
        pipeline.mapping = [
            ['#!uuid', 'Person.id']
        ]
        pipeline.save()
        self.assertEqual(
            pipeline.mapping_errors,
            [['*', 'It was not possible to connect to Aether Kernel Server.']]
        )
        self.assertEqual(pipeline.output, [])

    @mock.patch('aether.ui.api.utils.utils.test_connection', new=mock_return_true)
    def test__pipeline__save__with_errors(self):
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
            input=INPUT_SAMPLE,
        )
        EntityType.objects.create(
            pipeline=pipeline,
            name='Person',
            payload=ENTITY_SAMPLE,
        )

        pipeline.mapping = [
            ['#!uuid', 'Person.id'],
            ['$.firstName', 'Person.firstName'],
        ]

        # with error
        response = MockResponse({}, 500)
        with mock.patch('requests.post', return_value=response):
            pipeline.save()
            self.assertEqual(
                pipeline.mapping_errors,
                [['*', f'It was not possible to validate the pipeline: 500']]
            )
            self.assertEqual(pipeline.output, [])

        # with another response without the expected keys
        response = MockResponse({
            'entities_2': 'something',
            'mapping_errors_2': 'something else',
        }, 200)
        with mock.patch('requests.post', return_value=response):
            pipeline.save()
            self.assertEqual(pipeline.mapping_errors, [])
            self.assertEqual(pipeline.output, [])

    @mock.patch('aether.ui.api.utils.utils.test_connection', new=mock_return_true)
    def test__pipeline__save__validated(self):
        pipeline = Pipeline.objects.create(
            name='Pipeline test',
            input=INPUT_SAMPLE,
            mapping=[
                ['#!uuid', 'Person.id'],
                ['$.firstName', 'Person.firstName'],
            ],
        )

        # creating an entity type triggers the validation
        response = MockResponse({
            'entities': 'something',
            'mapping_errors': 'something else',
        }, 200)
        with mock.patch('requests.post', return_value=response):
            entity_type = EntityType.objects.create(
                pipeline=pipeline,
                name='Person',
                payload=ENTITY_SAMPLE,
            )
            self.assertEqual(pipeline.mapping_errors, 'something else')
            self.assertEqual(pipeline.output, 'something')

        # saving entity triggers validation
        response = MockResponse({
            'entities': 'nothing',
            'mapping_errors': 'nothing else',
        }, 200)
        with mock.patch('requests.post', return_value=response):
            entity_type.save()
            self.assertEqual(pipeline.mapping_errors, 'nothing else')
            self.assertEqual(pipeline.output, 'nothing')

        # delete the entity type also triggers the validation
        entity_type.delete()
        self.assertEqual(pipeline.mapping_errors, [])
        self.assertEqual(pipeline.output, [])
