import json
import mock

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from . import (PIPELINE_EXAMPLE, PIPELINE_EXAMPLE_WITH_MAPPING_ERRORS)

from ..models import Pipeline
from .. import utils


RESPONSE_MOCK = mock.Mock(status_code=200)
APP_TOKEN_MOCK = mock.Mock(base_url='http://test', token='ABCDEFGH')


class ViewsTest(TestCase):

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
        self.assertEqual(response_data['name'], 'Pipeline')
        # initial status without meaningful data
        self.assertEqual(len(response_data['mapping_errors']), 0)
        self.assertEqual(len(response_data['output']), 0)

        url_patch = reverse('pipeline-detail', kwargs={'pk': response_data['id']})

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

    def test_view_pipeline___publish(self):
        url = reverse('pipeline-list')
        data = json.dumps(PIPELINE_EXAMPLE)
        response = self.client.post(url, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        pipeline_id = response_data['id']
        self.assertEqual(response_data['name'], 'Pipeline Example')
        url = reverse('pipeline-publish', args=[pipeline_id])
        response = self.client.post(url, {'project_name': 'Aux'})
        response_data = json.loads(response.content)

        # make sure kernel db is clean for this to pass
        self.assertEqual(response.status_code, 200)
        pipeline = Pipeline.objects.get(pk=pipeline_id)
        self.assertEqual(len(pipeline.kernel_refs), 4)
        self.assertEqual(len(pipeline.kernel_refs['schema']), 2)

        outcome = {
                    'successful': [],
                    'error': [],
                    'exists': []
                }
        outcome = utils.publish_preflight(pipeline, 'Aux', outcome)
        self.assertEqual(len(outcome['error']), 0)
        self.assertEqual(len(outcome['exists']), 3)

        url = reverse('pipeline-list')
        data = json.dumps(PIPELINE_EXAMPLE_WITH_MAPPING_ERRORS)
        response = self.client.post(url, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        pipeline_id = response_data['id']
        url = reverse('pipeline-publish', args=[pipeline_id])
        response = self.client.post(url)
        response_data = json.loads(response.content)
        self.assertIn(response_data['error'][0],
                      'Mappings have errors')

        url = reverse('pipeline-list')
        data = json.dumps({
            'name': 'pipeline1'
        })
        response = self.client.post(url, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        pipeline_id = response_data['id']
        pipeline2 = Pipeline.objects.get(pk=pipeline_id)
        pipeline2.kernel_refs = pipeline.kernel_refs
        pipeline2.save()
        url = reverse('pipeline-publish', args=[pipeline_id])
        response = self.client.post(url, {'project_name': 'Aux 1'})
        response_data = json.loads(response.content)
        self.assertGreater(len(response_data['exists']), 0)
        map_data = json.loads(data)
        self.assertIn(response_data['exists'][0][map_data['name']],
                      'Mapping with id {} exists'.format(pipeline.kernel_refs['mapping']))

        url = reverse('pipeline-list')
        data = json.dumps({
            'name': 'pipeline 2',
            'entity_types': [{'name': 'Screening', 'type': 'record', 'fields':
                             [
                                {'name': 'id', 'type': 'string'},
                                {'name': 'firstName', 'type': 'string'}
                             ]
                        }]
        })
        response = self.client.post(url, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        pipeline_id = response_data['id']
        pipeline2 = Pipeline.objects.get(pk=pipeline_id)
        pipeline2.kernel_refs = pipeline.kernel_refs
        pipeline2.save()
        url = reverse('pipeline-publish', args=[pipeline_id])
        response = self.client.post(url, {'project_name': 'Aux 1'})
        response_data = json.loads(response.content)
        self.assertGreater(len(response_data['exists']), 0)
        self.assertIn(response_data['exists'][0]['Screening'],
                      '{} schema with id {} exists'.format('Screening',
                                                           pipeline.kernel_refs['schema']['Screening']))

        url = reverse('pipeline-list')
        data = json.dumps({
            'name': 'pipeline 3',
            'entity_types': [{'name': 'Screening', 'type': 'record', 'fields':
                             [
                                {'name': 'id', 'type': 'string'},
                                {'name': 'firstName', 'type': 'string'}
                             ]
                        }]
        })
        response = self.client.post(url, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        pipeline_id = response_data['id']
        pipeline2 = Pipeline.objects.get(pk=pipeline_id)
        url = reverse('pipeline-publish', args=[pipeline_id])
        response = self.client.post(url, {'project_name': 'Aux 1'})
        response_data = json.loads(response.content)
        self.assertGreater(len(response_data['exists']), 0)

        url = reverse('pipeline-publish', args=[str(pipeline_id) + 'wrong'])
        response = self.client.post(url, {'project_name': 'Aux 1'})
        response_data = json.loads(response.content)

        pipeline.kernel_refs = {}
        pipeline.save()

        outcome = {
                    'successful': [],
                    'error': [],
                    'exists': []
                }
        outcome = utils.publish_preflight(pipeline, 'Aux', outcome)
        self.assertEqual(len(outcome['exists']), 5)

    def test_view_pipeline__publish(self):
        pipeline = Pipeline.objects.create(
            name='Pipeline Mock 2',
            schema={'name': 'test', 'type': 'record', 'fields':
                    [{'name': 'name', 'type': 'string'}]},
            input={'test': {'name': 'myValue'}},
            entity_types=[{'name': 'Test', 'type': 'record', 'fields':
                          [{'type': 'string', 'name': 'name'}, {'type': 'string', 'name': 'id'}]}],
            mapping=[{'source': 'test.name', 'destination': 'Test.name'},
                     {'source': '#!uuid', 'destination': 'Test.id'}],
            output={'id': 'uuids', 'name': 'a-name'}
        )
        outcome = utils.publish_pipeline(pipeline, 'Aux')
        self.assertIn(outcome['successful'][0],
                      'Existing Aux project used')
        outcome = utils.publish_pipeline(pipeline, 'Aux')
        self.assertEqual(len(outcome['error']), 2)
        url = reverse('pipeline-publish', args=[str(pipeline.id)])
        response = self.client.post(url, {'project_name': 'Aux', 'overwrite': True})
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data['successful']), 4)

        pipeline.kernel_refs = {}
        pipeline.save()
        url = reverse('pipeline-publish', args=[str(pipeline.id)])
        response = self.client.post(url, {'project_name': 'Aux', 'overwrite': True})
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data['successful']), 3)

    def test_view_pipeline_fetch(self):
        url = reverse('pipeline-fetch')
        response = self.client.post(url, content_type='application/json')
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 2)
        self.assertEqual(len(response_data[0]['entity_types']), 2)

        # Ensure linked mappings are not recreated
        response = self.client.post(url, content_type='application/json')
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 2)
