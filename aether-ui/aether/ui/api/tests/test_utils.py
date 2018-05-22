import ast

from django.test import TestCase

from . import PIPELINE_EXAMPLE_1
from ..models import Pipeline
from .. import utils


class ViewsTest(TestCase):
    project_id = ''

    def test_kernel_data_request(self):
        result = utils.kernel_data_request('projects', 'get')
        self.assertIn('count', result)
        with self.assertRaises(Exception):
            utils.kernel_data_request('projects', 'post', {'wrong-input': 'tests'})

    def test_create_new_kernel_object(self):
        pipeline = Pipeline.objects.create(
            name=PIPELINE_EXAMPLE_1['name'],
            schema=PIPELINE_EXAMPLE_1['schema'],
            input=PIPELINE_EXAMPLE_1['input'],
            entity_types=PIPELINE_EXAMPLE_1['entity_types'],
            mapping=PIPELINE_EXAMPLE_1['mapping'],
            output=PIPELINE_EXAMPLE_1['output'],
            kernel_refs=PIPELINE_EXAMPLE_1['kernel_refs']
        )
        project_data = {
                        'revision': '123',
                        'name': 'Test-Project',
                        'salad_schema': '[]',
                        'jsonld_context': '[]',
                        'rdf_definition': '[]'
                      }
        entity_type = PIPELINE_EXAMPLE_1['entity_types'][2]
        schema_data = {
                        'revision': '123',
                        'name': entity_type['name'],
                        'type': entity_type['type'],
                        'definition': entity_type
                      }
        # must run on an empty kernel db
        utils.create_new_kernel_object('project', pipeline, project_data)
        self.project_id = pipeline.kernel_refs['project']
        utils.create_new_kernel_object('schema', pipeline, schema_data)
        pipeline = Pipeline.objects.get(pk=pipeline.id)
        self.assertIn('PersonX', pipeline.kernel_refs['schema'])
        self.assertIn('PersonX', pipeline.kernel_refs['projectSchema'])
        utils.create_project_schema_object('Test-Schema-Project', pipeline,
                                           pipeline.kernel_refs['schema']['PersonX'],
                                           'PersonX')
        utils.create_project_schema_object('Test-Schema-Project-1', pipeline,
                                           pipeline.kernel_refs['schema']['PersonX'],
                                           'PersonC')
        pipeline = Pipeline.objects.get(pk=pipeline.id)
        self.assertIn('PersonC', pipeline.kernel_refs['projectSchema'])

        with self.assertRaises(Exception) as exc:
            utils.create_new_kernel_object('project', pipeline, {}, 'Aux-test')
        exception = ast.literal_eval(str(exc.exception))
        self.assertEqual(exception['object_name'], 'unknown')
        self.assertFalse(utils.is_object_linked(pipeline.kernel_refs, 'schema', 'Person'))

    def test_convert_entity_types(self):
        with self.assertRaises(Exception) as exc:
            utils.convertEntityTypes({'Person': '123456'})
            exception = ast.literal_eval(str(exc.exception))
            self.assertEqual(exception['object_name'], 'unknown')

    def test_update_kernel_object(self):
        with self.assertRaises(Exception):
            data = {
                'name': 'Aux-test'
            }
            utils.update_kernel_object('project', self.project_id, data)

        with self.assertRaises(Exception):
            data = {}
            utils.update_kernel_object('project', self.project_id, data)
