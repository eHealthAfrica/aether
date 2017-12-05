import mock
from django.test import TestCase

from .. import utils

AETHER_CORE_URL_MOCK = 'http://core'
AETHER_CORE_URL_TEST_MOCK = 'http://core-test'
AETHER_CORE_TOKEN_MOCK = 'mock-valid-token'
AETHER_ENV_MOCK = {
    'AETHER_CORE_URL': AETHER_CORE_URL_MOCK,
    'AETHER_CORE_URL_TEST': AETHER_CORE_URL_TEST_MOCK,
    'AETHER_CORE_TOKEN': AETHER_CORE_TOKEN_MOCK,
}


class UtilsTests(TestCase):

    @mock.patch.dict('os.environ', AETHER_ENV_MOCK)
    def test__get_mapping_url_testing(self):
        self.assertEqual(
            utils.get_mappings_url(),
            'http://core-test/mappings/'
        )
        self.assertEqual(
            utils.get_mappings_url(1),
            'http://core-test/mappings/1'
        )
        self.assertEqual(
            utils.get_mapping_responses_url(1),
            'http://core-test/mappings/1/responses/'
        )
        self.assertEqual(
            utils.get_mapping_responses_url(1, 2),
            'http://core-test/mappings/1/responses/2/'
        )
        self.assertRaises(
            Exception,
            utils.get_mapping_responses_url,
            mapping_id=None,
        )

    @mock.patch.dict('os.environ', {'TESTING': ''})
    @mock.patch.dict('os.environ', AETHER_ENV_MOCK)
    def test__get_mapping_url__no_testing(self):
        self.assertEqual(
            utils.get_mappings_url(),
            'http://core/mappings/'
        )
        self.assertEqual(
            utils.get_mappings_url(1),
            'http://core/mappings/1'
        )
        self.assertEqual(
            utils.get_mapping_responses_url(1),
            'http://core/mappings/1/responses/'
        )
        self.assertEqual(
            utils.get_mapping_responses_url(1, 2),
            'http://core/mappings/1/responses/2/'
        )
        self.assertRaises(
            Exception,
            utils.get_mapping_responses_url,
            mapping_id=None,
        )

    @mock.patch('requests.head', return_value=mock.Mock(status_code=403))
    @mock.patch('requests.get', return_value=mock.Mock(status_code=200))
    @mock.patch.dict('os.environ', AETHER_ENV_MOCK)
    def test__test_connection_testing_env(self, mock_get, mock_head):
        self.assertTrue(utils.test_connection())
        self.assertNotEqual(utils.get_auth_header(), None)

    def test__test_connection_env_fail(self):
        with mock.patch.dict('os.environ', {
            'AETHER_CORE_URL': '',
            'AETHER_CORE_URL_TEST': '',
            'AETHER_CORE_TOKEN': '',
        }):
            self.assertFalse(utils.test_connection())
            self.assertEqual(utils.get_auth_header(), None)

        with mock.patch.dict('os.environ', {
            'AETHER_CORE_URL': AETHER_CORE_URL_MOCK,
            'AETHER_CORE_URL_TEST': AETHER_CORE_URL_TEST_MOCK,
            'AETHER_CORE_TOKEN': '',
        }):
            self.assertFalse(utils.test_connection())
            self.assertEqual(utils.get_auth_header(), None)

        with mock.patch.dict('os.environ', {
            'AETHER_CORE_URL': '',
            'AETHER_CORE_URL_TEST': '',
            'AETHER_CORE_TOKEN': AETHER_CORE_TOKEN_MOCK,
        }):
            self.assertFalse(utils.test_connection())
            self.assertEqual(utils.get_auth_header(), None)

    @mock.patch('requests.head', return_value=mock.Mock(status_code=404))
    @mock.patch.dict('os.environ', AETHER_ENV_MOCK)
    def test__test_connection_head_fail(self, mock_head):
        with mock.patch.dict('os.environ', AETHER_ENV_MOCK):
            self.assertFalse(utils.test_connection())
            mock_head.assert_called_with(AETHER_CORE_URL_TEST_MOCK)

    @mock.patch('requests.head', return_value=mock.Mock(status_code=403))
    @mock.patch('requests.get', return_value=mock.Mock(status_code=401))
    @mock.patch.dict('os.environ', AETHER_ENV_MOCK)
    def test__test_connection_get_fail(self, mock_get, mock_head):
        with mock.patch.dict('os.environ', AETHER_ENV_MOCK):
            self.assertFalse(utils.test_connection())
            self.assertEqual(utils.get_auth_header(), None)
            mock_head.assert_called_with(AETHER_CORE_URL_TEST_MOCK)
            mock_get.assert_called_with(
                AETHER_CORE_URL_TEST_MOCK,
                headers={
                    'Authorization': 'Token {}'.format(AETHER_CORE_TOKEN_MOCK)
                },
            )

    @mock.patch.dict('os.environ', AETHER_ENV_MOCK)
    def test_submit_to_core__without_mapping_id(self):
        self.assertRaises(
            Exception,
            utils.submit_to_core,
            response={},
            mapping_id=None,
        )

    @mock.patch.dict('os.environ', AETHER_ENV_MOCK)
    def test_submit_to_core__without_response(self):
        self.assertRaises(
            Exception,
            utils.submit_to_core,
            response=None,
            mapping_id=1,
        )

    @mock.patch('requests.put')
    @mock.patch('requests.post')
    @mock.patch.dict('os.environ', AETHER_ENV_MOCK)
    def test_submit_to_core__without_response_id(self, mock_post, mock_put):
        utils.submit_to_core(response={'_id': 'a'}, mapping_id=1, response_id=None)
        mock_put.assert_not_called()
        mock_post.assert_called()

    @mock.patch('requests.put')
    @mock.patch('requests.post')
    @mock.patch.dict('os.environ', AETHER_ENV_MOCK)
    def test_submit_to_core__with_response_id(self, mock_post, mock_put):
        utils.submit_to_core(response={'_id': 'a'}, mapping_id=1, response_id=1)
        mock_put.assert_called()
        mock_post.assert_not_called()

    @mock.patch.dict('os.environ', AETHER_ENV_MOCK)
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
