import mock

from django.test import TestCase


class ViewsTest(TestCase):

    def test__check_kernel(self):
        with mock.patch('aether.common.kernel.utils.test_connection', return_value=False):
            response = self.client.get('/check-kernel')
            self.assertEqual(
                response.content.decode(),
                'Always Look on the Bright Side of Life!!!',
            )

        with mock.patch('aether.common.kernel.utils.test_connection', return_value=True):
            response = self.client.get('/check-kernel')
            self.assertEqual(
                response.content.decode(),
                'Brought to you by eHealth Africa - good tech for hard places',
            )

    def test_api_pass(self):
        response = self.client.post('/api-pass', {'client_id': 'a_test_client_id'})
        self.assertEqual(200, response.status_code)
