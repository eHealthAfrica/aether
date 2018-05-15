import mock
import json

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase, RequestFactory

from ..views import TokenProxyView
from . import (PIPELINE_EXAMPLE, PIPELINE_EXAMPLE_WITH_MAPPING_ERRORS)
from ..models import Pipeline


RESPONSE_MOCK = mock.Mock(status_code=200)
APP_TOKEN_MOCK = mock.Mock(base_url='http://test', token='ABCDEFGH')


class ViewsTest(TestCase):

    def setUp(self):
        username = 'test'
        email = 'test@example.com'
        password = 'testtest'

        self.user = get_user_model().objects.create_user(username, email, password)
        self.view = TokenProxyView.as_view(app_name='kernel')

    @mock.patch('aether.ui.api.models.UserTokens.get_or_create_user_app_token')
    def test_proxy_view_without_valid_app(self, mock_test_conn):
        request = RequestFactory().get('/go_to_proxy')
        request.user = self.user
        view_unknown = TokenProxyView.as_view(app_name='unknown')

        self.assertRaises(
            RuntimeError,
            view_unknown,
            request,
            path='to-get',
        )
        mock_test_conn.assert_not_called()

    @mock.patch('aether.ui.api.models.UserTokens.get_or_create_user_app_token', return_value=None)
    def test_proxy_view_without_valid_token(self, mock_test_conn):
        request = RequestFactory().get('/go_to_proxy')
        request.user = self.user

        self.assertRaises(
            RuntimeError,
            self.view,
            request,
            path='to-get',
        )
        mock_test_conn.assert_called_once()

    @mock.patch('aether.ui.api.models.UserTokens.get_or_create_user_app_token',
                return_value=APP_TOKEN_MOCK)
    @mock.patch('requests.request', return_value=RESPONSE_MOCK)
    def test_proxy_view_delete(self, mock_request, mock_test_conn):
        request = RequestFactory().delete('/go_to_proxy')
        request.user = self.user
        response = self.view(request, path='to-delete')

        self.assertEqual(response.status_code, 200)
        mock_test_conn.assert_called_once()
        mock_request.assert_called_once_with(
            method='DELETE',
            url='http://test/to-delete',
            data=None,
            headers={'Cookie': '', 'Authorization': 'Token ABCDEFGH'}
        )

    @mock.patch('aether.ui.api.models.UserTokens.get_or_create_user_app_token',
                return_value=APP_TOKEN_MOCK)
    @mock.patch('requests.request', return_value=RESPONSE_MOCK)
    def test_proxy_view_get(self, mock_request, mock_test_conn):
        request = RequestFactory().get('/go_to_proxy')
        request.user = self.user
        response = self.view(request, path='/to-get')

        self.assertEqual(response.status_code, 200)
        mock_test_conn.assert_called_once()
        mock_request.assert_called_once_with(
            method='GET',
            url='http://test/to-get',
            data=None,
            headers={'Cookie': '', 'Authorization': 'Token ABCDEFGH'}
        )

    @mock.patch('aether.ui.api.models.UserTokens.get_or_create_user_app_token',
                return_value=APP_TOKEN_MOCK)
    @mock.patch('requests.request', return_value=RESPONSE_MOCK)
    def test_proxy_view_head(self, mock_request, mock_test_conn):
        request = RequestFactory().head('/go_to_proxy')
        request.user = self.user
        response = self.view(request, path='proxy')

        self.assertEqual(response.status_code, 200)
        mock_test_conn.assert_called_once()
        mock_request.assert_called_once_with(
            method='HEAD',
            url='http://test/proxy',
            data=None,
            headers={'Cookie': '', 'Authorization': 'Token ABCDEFGH'}
        )

    @mock.patch('aether.ui.api.models.UserTokens.get_or_create_user_app_token',
                return_value=APP_TOKEN_MOCK)
    @mock.patch('requests.request', return_value=RESPONSE_MOCK)
    def test_proxy_view_options(self, mock_request, mock_test_conn):
        request = RequestFactory().options('/go_to_proxy')
        request.user = self.user
        response = self.view(request, path='/to-options')

        self.assertEqual(response.status_code, 200)
        mock_test_conn.assert_called_once()
        mock_request.assert_called_once_with(
            method='OPTIONS',
            url='http://test/to-options',
            data=None,
            headers={'Cookie': '', 'Authorization': 'Token ABCDEFGH'}
        )

    @mock.patch('aether.ui.api.models.UserTokens.get_or_create_user_app_token',
                return_value=APP_TOKEN_MOCK)
    @mock.patch('requests.request', return_value=RESPONSE_MOCK)
    def test_proxy_view_patch(self, mock_request, mock_test_conn):
        request = RequestFactory().patch('/go_to_proxy')
        request.user = self.user
        response = self.view(request, path='to-patch')

        self.assertEqual(response.status_code, 200)
        mock_test_conn.assert_called_once()
        mock_request.assert_called_once_with(
            method='PATCH',
            url='http://test/to-patch',
            data=None,
            headers={'Cookie': '', 'Authorization': 'Token ABCDEFGH'}
        )

    @mock.patch('aether.ui.api.models.UserTokens.get_or_create_user_app_token',
                return_value=APP_TOKEN_MOCK)
    @mock.patch('requests.request', return_value=RESPONSE_MOCK)
    def test_proxy_view_post(self, mock_request, mock_test_conn):
        request = RequestFactory().post('/go_to_proxy',
                                        data=json.dumps({'a': 1}),
                                        content_type='application/json')
        request.user = self.user
        response = self.view(request, path='posting')

        self.assertEqual(response.status_code, 200)
        mock_test_conn.assert_called_once()
        mock_request.assert_called_once_with(
            method='POST',
            url='http://test/posting',
            data=b'{"a": 1}',
            headers={
                'Cookie': '',
                'Authorization': 'Token ABCDEFGH',
                'Content-Type': 'application/json',
            }
        )

    @mock.patch('aether.ui.api.models.UserTokens.get_or_create_user_app_token',
                return_value=APP_TOKEN_MOCK)
    @mock.patch('requests.request', return_value=RESPONSE_MOCK)
    def test_proxy_view_put(self, mock_request, mock_test_conn):
        request = RequestFactory().put('/go_to_proxy', data='something')
        request.user = self.user
        response = self.view(request, path='putting')

        self.assertEqual(response.status_code, 200)
        mock_test_conn.assert_called_once()
        mock_request.assert_called_once_with(
            method='PUT',
            url='http://test/putting',
            data=b'something',
            headers={
                'Cookie': '',
                'Authorization': 'Token ABCDEFGH',
                'Content-Type': 'application/octet-stream',
            }
        )

    def test_tokens_required(self):
        tokens_page = reverse('tokens')

        # if no logged in user...
        url = reverse('check-tokens')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/accounts/login/?next=/check-tokens')

        self.assertTrue(self.client.login(username='test', password='testtest'))

        # redirects to `tokens` url if something unexpected happens
        with mock.patch('aether.ui.api.models.UserTokens.get_or_create_user_app_token',
                        side_effect=RuntimeError):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, tokens_page)

        # redirects to `tokens` url if the tokens are not valid
        with mock.patch('aether.ui.api.models.UserTokens.get_or_create_user_app_token',
                        return_value=None):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, tokens_page)

        # with valid tokens it does not redirect
        with mock.patch('aether.ui.api.models.UserTokens.get_or_create_user_app_token',
                        return_value=APP_TOKEN_MOCK) as mock_get_app_token:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(mock_get_app_token.call_count, 1)
            self.assertEqual(mock_get_app_token.call_args_list,
                             [
                                 mock.call(self.user, 'kernel'),
                             ])

    @mock.patch('aether.ui.api.models.UserTokens.get_or_create_user_app_token',
                return_value=APP_TOKEN_MOCK)
    @mock.patch('requests.request', return_value=RESPONSE_MOCK)
    def test_proxy_view_put_but_post(self, mock_request, mock_test_conn):
        request = RequestFactory().put('/go_to_example',
                                       data='something',
                                       **{'HTTP_X_METHOD': 'POST'})
        request.user = self.user
        response = self.view(request, path='fake_put')

        self.assertEqual(response.status_code, 200)
        mock_test_conn.assert_called_once()
        mock_request.assert_called_once_with(
            method='POST',
            url='http://test/fake_put',
            data=b'something',
            headers={
                'Cookie': '',
                'Authorization': 'Token ABCDEFGH',
                'Content-Type': 'application/octet-stream',
                'X-Method': 'POST',
            }
        )

    @mock.patch('aether.ui.api.models.UserTokens.get_or_create_user_app_token',
                return_value=APP_TOKEN_MOCK)
    @mock.patch('requests.request', return_value=RESPONSE_MOCK)
    def test_proxy_view_put_but_other(self, mock_request, mock_test_conn):
        request = RequestFactory().put('/go_to_example',
                                       data='something',
                                       **{'HTTP_X_METHOD': 'GET'})
        request.user = self.user
        response = self.view(request, path='fake_put')

        self.assertEqual(response.status_code, 200)
        mock_test_conn.assert_called_once()
        mock_request.assert_called_once_with(
            method='PUT',
            url='http://test/fake_put',
            data=b'something',
            headers={
                'Cookie': '',
                'Authorization': 'Token ABCDEFGH',
                'Content-Type': 'application/octet-stream',
                'X-Method': 'GET',
            }
        )

    def test_view_01_publish_pipeline(self):
        username = 'test'
        password = 'testtest'
        self.client.login(username=username, password=password)
        url = reverse('ui:pipeline-list')
        data = json.dumps(PIPELINE_EXAMPLE)
        response = self.client.post(url, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        pipeline_id = response_data['id']
        self.assertEqual(response_data['name'], 'Pipeline Mock 1')
        url = reverse('ui:pipeline-publish', args=[pipeline_id])
        response = self.client.post(url, {'project_name': 'Aux'})
        response_data = json.loads(response.content)

        # make sure kernel db is clean for this to pass
        self.assertEqual(response.status_code, 200)
        pipeline = Pipeline.objects.get(pk=pipeline_id)
        self.assertEqual(len(pipeline.kernel_refs), 4)
        self.assertEqual(len(pipeline.kernel_refs['schema']), 2)

        url = reverse('ui:pipeline-list')
        data = json.dumps(PIPELINE_EXAMPLE_WITH_MAPPING_ERRORS)
        response = self.client.post(url, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        pipeline_id = response_data['id']
        url = reverse('ui:pipeline-publish', args=[pipeline_id])
        response = self.client.post(url)
        response_data = json.loads(response.content)
        self.assertIn(response_data['info']['failed'][0]['message'],
                      'Mappings have errors')

        url = reverse('ui:pipeline-list')
        data = json.dumps({
            'name': 'pipeline 1'
        })
        response = self.client.post(url, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        pipeline_id = response_data['id']
        pipeline2 = Pipeline.objects.get(pk=pipeline_id)
        pipeline2.kernel_refs = pipeline.kernel_refs
        pipeline2.save()
        url = reverse('ui:pipeline-publish', args=[pipeline_id])
        response = self.client.post(url, {'project_name': 'Aux 1'})
        response_data = json.loads(response.content)
        self.assertGreater(len(response_data['info']['exists']), 0)
        self.assertIn(response_data['info']['exists'][0]['message'],
                      'Mapping with id {} exists'.format(pipeline.kernel_refs['mapping']))

        url = reverse('ui:pipeline-list')
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
        url = reverse('ui:pipeline-publish', args=[pipeline_id])
        response = self.client.post(url, {'project_name': 'Aux 1'})
        response_data = json.loads(response.content)
        self.assertGreater(len(response_data['info']['exists']), 0)
        self.assertIn(response_data['info']['exists'][0]['message'],
                      '{} schema with id {} exists'.format('Screening',
                                                           pipeline.kernel_refs['schema']['Screening']))

        url = reverse('ui:pipeline-list')
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
        url = reverse('ui:pipeline-publish', args=[pipeline_id])
        response = self.client.post(url, {'project_name': 'Aux 1'})
        response_data = json.loads(response.content)
        self.assertGreater(len(response_data['info']['failed']), 0)

        url = reverse('ui:pipeline-publish', args=[str(pipeline_id) + 'wrong'])
        response = self.client.post(url, {'project_name': 'Aux 1'})
        response_data = json.loads(response.content)

    def test_view_02_fetch_pipeline(self):
        username = 'test'
        password = 'testtest'
        self.client.login(username=username, password=password)
        url = reverse('ui:pipeline-fetch')
        response = self.client.get(url, content_type='application/json')
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(len(response_data[0]['entity_types']), 2)

        # Ensure linked mappings are not recreated
        response = self.client.get(url, content_type='application/json')
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 1)
