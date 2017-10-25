import mock
from django.test import TestCase

from .. import utils

GATHER_CORE_URL_MOCK = 'http://core'
GATHER_CORE_URL_TEST_MOCK = 'http://core-test'
GATHER_CORE_TOKEN_MOCK = 'mock-valid-token'
GATHER_ENV_MOCK = {
    'GATHER_CORE_URL': GATHER_CORE_URL_MOCK,
    'GATHER_CORE_URL_TEST': GATHER_CORE_URL_TEST_MOCK,
    'GATHER_CORE_TOKEN': GATHER_CORE_TOKEN_MOCK,
}


class UtilsTests(TestCase):

    @mock.patch.dict('os.environ', GATHER_ENV_MOCK)
    def test__get_survey_url_testing(self):
        self.assertEqual(
            utils.get_surveys_url(),
            'http://core-test/surveys/'
        )
        self.assertEqual(
            utils.get_surveys_url(1),
            'http://core-test/surveys/1'
        )
        self.assertEqual(
            utils.get_survey_responses_url(1),
            'http://core-test/surveys/1/responses/'
        )
        self.assertEqual(
            utils.get_survey_responses_url(1, 2),
            'http://core-test/surveys/1/responses/2/'
        )
        self.assertRaises(
            Exception,
            utils.get_survey_responses_url,
            survey_id=None,
        )

    @mock.patch.dict('os.environ', {'TESTING': ''})
    @mock.patch.dict('os.environ', GATHER_ENV_MOCK)
    def test__get_survey_url__no_testing(self):
        self.assertEqual(
            utils.get_surveys_url(),
            'http://core/surveys/'
        )
        self.assertEqual(
            utils.get_surveys_url(1),
            'http://core/surveys/1'
        )
        self.assertEqual(
            utils.get_survey_responses_url(1),
            'http://core/surveys/1/responses/'
        )
        self.assertEqual(
            utils.get_survey_responses_url(1, 2),
            'http://core/surveys/1/responses/2/'
        )
        self.assertRaises(
            Exception,
            utils.get_survey_responses_url,
            survey_id=None,
        )

    @mock.patch('requests.head', return_value=mock.Mock(status_code=403))
    @mock.patch('requests.get', return_value=mock.Mock(status_code=200))
    @mock.patch.dict('os.environ', GATHER_ENV_MOCK)
    def test__test_connection_testing_env(self, mock_get, mock_head):
        self.assertTrue(utils.test_connection())
        self.assertNotEqual(utils.get_auth_header(), None)

    def test__test_connection_env_fail(self):
        with mock.patch.dict('os.environ', {
            'GATHER_CORE_URL': '',
            'GATHER_CORE_URL_TEST': '',
            'GATHER_CORE_TOKEN': '',
        }):
            self.assertFalse(utils.test_connection())
            self.assertEqual(utils.get_auth_header(), None)

        with mock.patch.dict('os.environ', {
            'GATHER_CORE_URL': GATHER_CORE_URL_MOCK,
            'GATHER_CORE_URL_TEST': GATHER_CORE_URL_TEST_MOCK,
            'GATHER_CORE_TOKEN': '',
        }):
            self.assertFalse(utils.test_connection())
            self.assertEqual(utils.get_auth_header(), None)

        with mock.patch.dict('os.environ', {
            'GATHER_CORE_URL': '',
            'GATHER_CORE_URL_TEST': '',
            'GATHER_CORE_TOKEN': GATHER_CORE_TOKEN_MOCK,
        }):
            self.assertFalse(utils.test_connection())
            self.assertEqual(utils.get_auth_header(), None)

    @mock.patch('requests.head', return_value=mock.Mock(status_code=404))
    @mock.patch.dict('os.environ', GATHER_ENV_MOCK)
    def test__test_connection_head_fail(self, mock_head):
        with mock.patch.dict('os.environ', GATHER_ENV_MOCK):
            self.assertFalse(utils.test_connection())
            mock_head.assert_called_with(GATHER_CORE_URL_TEST_MOCK)

    @mock.patch('requests.head', return_value=mock.Mock(status_code=403))
    @mock.patch('requests.get', return_value=mock.Mock(status_code=401))
    @mock.patch.dict('os.environ', GATHER_ENV_MOCK)
    def test__test_connection_get_fail(self, mock_get, mock_head):
        with mock.patch.dict('os.environ', GATHER_ENV_MOCK):
            self.assertFalse(utils.test_connection())
            self.assertEqual(utils.get_auth_header(), None)
            mock_head.assert_called_with(GATHER_CORE_URL_TEST_MOCK)
            mock_get.assert_called_with(
                GATHER_CORE_URL_TEST_MOCK,
                headers={
                    'Authorization': 'Token {}'.format(GATHER_CORE_TOKEN_MOCK)
                },
            )

    @mock.patch.dict('os.environ', GATHER_ENV_MOCK)
    def test_submit_to_core__without_survey_id(self):
        self.assertRaises(
            Exception,
            utils.submit_to_core,
            response={},
            survey_id=None,
        )

    @mock.patch.dict('os.environ', GATHER_ENV_MOCK)
    def test_submit_to_core__without_response(self):
        self.assertRaises(
            Exception,
            utils.submit_to_core,
            response=None,
            survey_id=1,
        )

    @mock.patch('requests.put')
    @mock.patch('requests.post')
    @mock.patch.dict('os.environ', GATHER_ENV_MOCK)
    def test_submit_to_core__without_response_id(self, mock_post, mock_put):
        utils.submit_to_core(response={'_id': 'a'}, survey_id=1, response_id=None)
        mock_put.assert_not_called()
        mock_post.assert_called()

    @mock.patch('requests.put')
    @mock.patch('requests.post')
    @mock.patch.dict('os.environ', GATHER_ENV_MOCK)
    def test_submit_to_core__with_response_id(self, mock_post, mock_put):
        utils.submit_to_core(response={'_id': 'a'}, survey_id=1, response_id=1)
        mock_put.assert_called()
        mock_post.assert_not_called()

    @mock.patch.dict('os.environ', GATHER_ENV_MOCK)
    def test_get_all_docs(self):
        class MockResponse:
            def __init__(self, json_data):
                self.json_data = json_data

            def json(self):
                return self.json_data

            def raise_for_status(self):
                pass

        def my_side_effect(*args, **kwargs):
            if args[0] == 'http://first':
                return MockResponse(json_data={'results': [2], 'next': 'http://next'})
            else:
                return MockResponse(json_data={'results': [1], 'next': None})

        with mock.patch('requests.get', side_effect=my_side_effect) as mock_get:
            self.assertEqual(utils.get_all_docs('http://first'), [2, 1])
            mock_get.assert_called()
