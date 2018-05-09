import ast

from django.test import TestCase

from . import PIPELINE_EXAMPLE_1
from ..models import Pipeline
from ..utils import (kernel_data_request, create_new_kernel_object, is_object_linked,
                     create_project_schema_object)


class ViewsTest(TestCase):
    def test_kernel_data_request(self):
        result = kernel_data_request('projects', 'get')
        self.assertIn('count', result)
        with self.assertRaises(Exception):
            kernel_data_request('projects', 'post', {'wrong-input': 'tests'})

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
        create_new_kernel_object('project', pipeline, project_data)
        create_new_kernel_object('schema', pipeline, schema_data)
        pipeline = Pipeline.objects.get(pk=pipeline.id)
        self.assertIn('PersonX', pipeline.kernel_refs['schema'])
        create_project_schema_object('Test-Schema-Project', pipeline,
                                     pipeline.kernel_refs['schema']['PersonX'],
                                     'PersonX')
        self.assertIn('PersonX', pipeline.kernel_refs['projectSchema'])

        with self.assertRaises(Exception) as exc:
            create_new_kernel_object('project', pipeline, {}, 'Aux-test')
        exception = ast.literal_eval(str(exc.exception))
        self.assertEqual(exception['object_name'], 'unknown')
        self.assertFalse(is_object_linked(pipeline.kernel_refs, 'schema', 'Person'))
