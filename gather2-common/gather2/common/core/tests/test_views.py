import mock

from django.test import TestCase


class ViewsTest(TestCase):

    def test__check_core(self):
        with mock.patch('gather2.common.core.utils.test_connection', return_value=False):
            response = self.client.get('/check-core')
            self.assertEqual(
                response.content.decode(),
                'Always Look on the Bright Side of Life!!!',
            )

        with mock.patch('gather2.common.core.utils.test_connection', return_value=True):
            response = self.client.get('/check-core')
            self.assertEqual(
                response.content.decode(),
                'Brought to you by eHealth Africa - good tech for hard places',
            )
