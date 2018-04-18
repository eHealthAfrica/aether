import json

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase


class PipelineViewsTest(TestCase):

    def setUp(self):
        username = 'test'
        email = 'test@example.com'
        password = 'testtest'
        get_user_model().objects.create_user(username, email, password)
        self.assertTrue(self.client.login(username=username, password=password))

    def tearDown(self):
        self.client.logout()

    def test__pipeline__viewset(self):
        url = reverse('ui:pipeline-list')
        data = json.dumps({'name': 'Pipeline'})
        response = self.client.post(url, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        self.assertEqual(response_data['name'], 'Pipeline')
        # initial status without meaningful data
        self.assertEqual(len(response_data['mapping_errors']), 0)
        self.assertEqual(len(response_data['output']), 0)

        url_patch = reverse('ui:pipeline-detail', kwargs={'pk': response_data['id']})

        # patching a property will no alter the rest

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
