import mock
import json

from django.test import TestCase, RequestFactory

from ..views import ProxyView


RETURN_MOCK = mock.Mock(status_code=200)


class ViewsTest(TestCase):

    def setUp(self):
        self.viewWithoutToken = ProxyView.as_view(base_url='http://example.com')
        self.viewWithToken = ProxyView.as_view(base_url='http://example.com', token='ABCDEFGH')

    @mock.patch('requests.request', return_value=RETURN_MOCK)
    def test_proxy_view_delete(self, mock_request):
        request = RequestFactory().delete('/go_to_example')
        response = self.viewWithToken(request, path='to-delete')

        self.assertEqual(response.status_code, 200)
        mock_request.assert_called_once_with(
            method='DELETE',
            url='http://example.com/to-delete',
            data=None,
            headers={'Cookie': '', 'Authorization': 'Token ABCDEFGH'}
        )

    @mock.patch('requests.request', return_value=RETURN_MOCK)
    def test_proxy_view_delete_without_token(self, mock_request):
        request = RequestFactory().delete('/go_to_example')
        response = self.viewWithoutToken(request, path='/no-token')

        self.assertEqual(response.status_code, 200)
        mock_request.assert_called_once_with(
            method='DELETE',
            url='http://example.com/no-token',
            data=None,
            headers={'Cookie': ''}
        )

    @mock.patch('requests.request', return_value=RETURN_MOCK)
    def test_proxy_view_get(self, mock_request):
        request = RequestFactory().get('/go_to_example')
        response = self.viewWithToken(request, path='to-get')

        self.assertEqual(response.status_code, 200)
        mock_request.assert_called_once_with(
            method='GET',
            url='http://example.com/to-get',
            data=None,
            headers={'Cookie': '', 'Authorization': 'Token ABCDEFGH'}
        )

    @mock.patch('requests.request', return_value=RETURN_MOCK)
    def test_proxy_view_get_without_token(self, mock_request):
        request = RequestFactory().get('/go_to_example')
        response = self.viewWithoutToken(request, path='/no-token')

        self.assertEqual(response.status_code, 200)
        mock_request.assert_called_once_with(
            method='GET',
            url='http://example.com/no-token',
            data=None,
            headers={'Cookie': ''}
        )

    @mock.patch('requests.request', return_value=RETURN_MOCK)
    def test_proxy_view_head(self, mock_request):
        request = RequestFactory().head('/go_to_example')
        response = self.viewWithToken(request, path='proxy')

        self.assertEqual(response.status_code, 200)
        mock_request.assert_called_once_with(
            method='HEAD',
            url='http://example.com/proxy',
            data=None,
            headers={'Cookie': '', 'Authorization': 'Token ABCDEFGH'}
        )

    @mock.patch('requests.request', return_value=RETURN_MOCK)
    def test_proxy_view_options(self, mock_request):
        request = RequestFactory().options('/go_to_example')
        response = self.viewWithToken(request, path='to-options')

        self.assertEqual(response.status_code, 200)
        mock_request.assert_called_once_with(
            method='OPTIONS',
            url='http://example.com/to-options',
            data=None,
            headers={'Cookie': '', 'Authorization': 'Token ABCDEFGH'}
        )

    @mock.patch('requests.request', return_value=RETURN_MOCK)
    def test_proxy_view_patch(self, mock_request):
        request = RequestFactory().patch('/go_to_example')
        response = self.viewWithToken(request, path='to-patch')

        self.assertEqual(response.status_code, 200)
        mock_request.assert_called_once_with(
            method='PATCH',
            url='http://example.com/to-patch',
            data=None,
            headers={'Cookie': '', 'Authorization': 'Token ABCDEFGH'}
        )

    @mock.patch('requests.request', return_value=RETURN_MOCK)
    def test_proxy_view_post(self, mock_request):
        request = RequestFactory().post('/go_to_example',
                                        data=json.dumps({'a': 1}),
                                        content_type='application/json')
        response = self.viewWithToken(request, path='posting')

        self.assertEqual(response.status_code, 200)
        mock_request.assert_called_once_with(
            method='POST',
            url='http://example.com/posting',
            data=b'{"a": 1}',
            headers={
                'Cookie': '',
                'Authorization': 'Token ABCDEFGH',
                'Content-Type': 'application/json',
            }
        )

    @mock.patch('requests.request', return_value=RETURN_MOCK)
    def test_proxy_view_put(self, mock_request):
        request = RequestFactory().put('/go_to_example', data='something')
        response = self.viewWithToken(request, path='putting')

        self.assertEqual(response.status_code, 200)
        mock_request.assert_called_once_with(
            method='PUT',
            url='http://example.com/putting',
            data=b'something',
            headers={
                'Cookie': '',
                'Authorization': 'Token ABCDEFGH',
                'Content-Type': 'application/octet-stream',
            }
        )
