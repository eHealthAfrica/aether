import mock
from django.test import TestCase

from .. import core_utils

GATHER_CORE_URL_MOCK = 'http://mock-core:8000'
GATHER_CORE_TOKEN_MOCK = 'mock-valid-token'
GATHER_ENV_MOCK = {
    'GATHER_CORE_URL': GATHER_CORE_URL_MOCK,
    'GATHER_CORE_TOKEN': GATHER_CORE_TOKEN_MOCK,
}
GATHER_HEADER_MOCK = {'Authorization': 'Token {}'.format(GATHER_CORE_TOKEN_MOCK)}


class CoreTests(TestCase):

    def test__get_survey_url(self):
        with mock.patch.dict('os.environ', GATHER_ENV_MOCK):
            self.assertEqual(
                core_utils.get_survey_url(1),
                'http://mock-core:8000/surveys/1/responses/'
            )

    def test__test_connection_env_fail(self):
        with mock.patch.dict('os.environ', {
            'GATHER_CORE_URL': '',
            'GATHER_CORE_TOKEN': '',
        }):
            self.assertFalse(core_utils.test_connection())
            self.assertEqual(core_utils.get_auth_header(), None)

        with mock.patch.dict('os.environ', {
            'GATHER_CORE_URL': GATHER_CORE_URL_MOCK,
            'GATHER_CORE_TOKEN': '',
        }):
            self.assertFalse(core_utils.test_connection())
            self.assertEqual(core_utils.get_auth_header(), None)

        with mock.patch.dict('os.environ', {
            'GATHER_CORE_URL': '',
            'GATHER_CORE_TOKEN': GATHER_CORE_TOKEN_MOCK,
        }):
            self.assertFalse(core_utils.test_connection())
            self.assertEqual(core_utils.get_auth_header(), None)

        with mock.patch.dict('os.environ', GATHER_ENV_MOCK):
            self.assertFalse(core_utils.test_connection())
            self.assertEqual(core_utils.get_auth_header(), None)

    @mock.patch('requests.head', return_value=mock.Mock(status_code=404))
    def test__test_connection_head_fail(self, mock_head):
        with mock.patch.dict('os.environ', GATHER_ENV_MOCK):
            self.assertFalse(core_utils.test_connection())
            mock_head.assert_called_with(GATHER_CORE_URL_MOCK)

    @mock.patch('requests.head', return_value=mock.Mock(status_code=200))
    @mock.patch('requests.get', return_value=mock.Mock(status_code=401))
    def test__test_connection_get_fail(self, mock_get, mock_head):
        with mock.patch.dict('os.environ', GATHER_ENV_MOCK):
            self.assertFalse(core_utils.test_connection())
            self.assertEqual(core_utils.get_auth_header(), None)
            mock_head.assert_called_with(GATHER_CORE_URL_MOCK)
            mock_get.assert_called_with(
                GATHER_CORE_URL_MOCK + '/surveys.json',
                headers=GATHER_HEADER_MOCK,
            )

    @mock.patch('requests.head', return_value=mock.Mock(status_code=200))
    @mock.patch('requests.get', return_value=mock.Mock(status_code=200, content='OK'))
    def test__test_connection_ok(self, mock_get, mock_head):
        with mock.patch.dict('os.environ', GATHER_ENV_MOCK):
            self.assertTrue(core_utils.test_connection())
            self.assertEqual(core_utils.get_auth_header(), GATHER_HEADER_MOCK)
            mock_head.assert_called_with(GATHER_CORE_URL_MOCK)
            mock_get.assert_called_with(
                GATHER_CORE_URL_MOCK + '/surveys.json',
                headers=GATHER_HEADER_MOCK,
            )
