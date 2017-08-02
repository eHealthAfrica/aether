import mock
from django.test import TestCase

from .. import core_utils

GATHER_CORE_URL_MOCK = 'http://test'
GATHER_CORE_TOKEN_MOCK = 'mock-valid-token'
GATHER_ENV_MOCK = {
    'TESTING': 'true',
    'GATHER_CORE_URL_TEST': GATHER_CORE_URL_MOCK,
    'GATHER_CORE_TOKEN': GATHER_CORE_TOKEN_MOCK,
}


class CoreTests(TestCase):

    def test__get_core_urls(self):
        with mock.patch.dict('os.environ', {
            'TESTING': 'false',
            'GATHER_CORE_URL': GATHER_CORE_URL_MOCK,
        }):
            self.assertEqual(
                core_utils.get_surveys_url(),
                'http://test/surveys/'
            )
            self.assertEqual(
                core_utils.get_survey_responses_url(1),
                'http://test/surveys/1/responses/'
            )
            self.assertEqual(
                core_utils.get_survey_responses_url(1, 2),
                'http://test/surveys/1/responses/2/'
            )

    def test__test_connection_testing_env(self):
        self.assertTrue(core_utils.test_connection())
        self.assertNotEqual(core_utils.get_auth_header(), None)

    def test__test_connection_env_fail(self):
        with mock.patch.dict('os.environ', {
            'TESTING': 'false',
            'GATHER_CORE_URL': '',
            'GATHER_CORE_TOKEN': '',
        }):
            self.assertFalse(core_utils.test_connection())
            self.assertEqual(core_utils.get_auth_header(), None)

        with mock.patch.dict('os.environ', {
            'TESTING': 'false',
            'GATHER_CORE_TOKEN': '',
        }):
            self.assertFalse(core_utils.test_connection())
            self.assertEqual(core_utils.get_auth_header(), None)

        with mock.patch.dict('os.environ', {
            'TESTING': 'false',
            'GATHER_CORE_URL': '',
            'GATHER_CORE_TOKEN': GATHER_CORE_TOKEN_MOCK,
        }):
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
                '{}/surveys.json'.format(GATHER_CORE_URL_MOCK),
                headers={
                    'Authorization': 'Token {}'.format(GATHER_CORE_TOKEN_MOCK)
                },
            )

    @mock.patch('requests.put')
    @mock.patch('requests.post')
    def test_submit_to_core__without_response_id(self, mock_post, mock_put):
        core_utils.submit_to_core(response={'_id': 'a'}, survey_id=1, response_id=None)
        mock_put.assert_not_called()
        mock_post.assert_called()

    @mock.patch('requests.put')
    @mock.patch('requests.post')
    def test_submit_to_core__with_response_id(self, mock_post, mock_put):
        core_utils.submit_to_core(response={'_id': 'a'}, survey_id=1, response_id=1)
        mock_put.assert_called()
        mock_post.assert_not_called()
