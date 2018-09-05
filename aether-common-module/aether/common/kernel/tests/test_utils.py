# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import mock
from django.test import TestCase

from .. import utils

AETHER_KERNEL_URL_MOCK = 'http://kernel'
AETHER_KERNEL_URL_TEST_MOCK = 'http://kernel-test'
AETHER_KERNEL_TOKEN_MOCK = 'mock-valid-token'
AETHER_ENV_MOCK = {
    'AETHER_KERNEL_URL': AETHER_KERNEL_URL_MOCK,
    'AETHER_KERNEL_URL_TEST': AETHER_KERNEL_URL_TEST_MOCK,
    'AETHER_KERNEL_TOKEN': AETHER_KERNEL_TOKEN_MOCK,
}


class UtilsTests(TestCase):

    @mock.patch.dict('os.environ', AETHER_ENV_MOCK)
    def test__get_mapping_url_testing(self):
        self.assertEqual(
            utils.get_mappings_url(),
            'http://kernel-test/mappings/'
        )
        self.assertEqual(
            utils.get_mappings_url(1),
            'http://kernel-test/mappings/1/'
        )
        self.assertEqual(
            utils.get_submissions_url(),
            'http://kernel-test/submissions/'
        )
        self.assertEqual(
            utils.get_submissions_url(1),
            'http://kernel-test/submissions/1/'
        )
        self.assertEqual(
            utils.get_attachments_url(),
            'http://kernel-test/attachments/'
        )
        self.assertEqual(
            utils.get_attachments_url(1),
            'http://kernel-test/attachments/1/'
        )
        self.assertRaises(
            Exception,
            utils.get_submissions_url,
            mapping_id=None,
        )

    @mock.patch.dict('os.environ', {'TESTING': ''})
    @mock.patch.dict('os.environ', AETHER_ENV_MOCK)
    def test__get_mapping_url__no_testing(self):
        self.assertEqual(
            utils.get_mappings_url(),
            'http://kernel/mappings/'
        )
        self.assertEqual(
            utils.get_mappings_url(1),
            'http://kernel/mappings/1/'
        )
        self.assertEqual(
            utils.get_submissions_url(1),
            'http://kernel/submissions/1/'
        )
        self.assertEqual(
            utils.get_attachments_url(1),
            'http://kernel/attachments/1/'
        )

    @mock.patch('requests.head', return_value=mock.Mock(status_code=403))
    @mock.patch('requests.get', return_value=mock.Mock(status_code=200))
    @mock.patch.dict('os.environ', AETHER_ENV_MOCK)
    def test__test_connection_testing_env(self, mock_get, mock_head):
        self.assertTrue(utils.test_connection())
        self.assertNotEqual(utils.get_auth_header(), None)

    def test__test_connection_env_fail(self):
        with mock.patch.dict('os.environ', {
            'AETHER_KERNEL_URL': '',
            'AETHER_KERNEL_URL_TEST': '',
            'AETHER_KERNEL_TOKEN': '',
        }):
            self.assertFalse(utils.test_connection())
            self.assertEqual(utils.get_auth_header(), None)

        with mock.patch.dict('os.environ', {
            'AETHER_KERNEL_URL': AETHER_KERNEL_URL_MOCK,
            'AETHER_KERNEL_URL_TEST': AETHER_KERNEL_URL_TEST_MOCK,
            'AETHER_KERNEL_TOKEN': '',
        }):
            self.assertFalse(utils.test_connection())
            self.assertEqual(utils.get_auth_header(), None)

        with mock.patch.dict('os.environ', {
            'AETHER_KERNEL_URL': '',
            'AETHER_KERNEL_URL_TEST': '',
            'AETHER_KERNEL_TOKEN': AETHER_KERNEL_TOKEN_MOCK,
        }):
            self.assertFalse(utils.test_connection())
            self.assertEqual(utils.get_auth_header(), None)

    @mock.patch('requests.head', return_value=mock.Mock(status_code=404))
    @mock.patch.dict('os.environ', AETHER_ENV_MOCK)
    def test__test_connection_head_fail(self, mock_head):
        with mock.patch.dict('os.environ', AETHER_ENV_MOCK):
            self.assertFalse(utils.test_connection())
            mock_head.assert_called_with(AETHER_KERNEL_URL_TEST_MOCK)

    @mock.patch('requests.head', return_value=mock.Mock(status_code=403))
    @mock.patch('requests.get', return_value=mock.Mock(status_code=401))
    @mock.patch.dict('os.environ', AETHER_ENV_MOCK)
    def test__test_connection_get_fail(self, mock_get, mock_head):
        with mock.patch.dict('os.environ', AETHER_ENV_MOCK):
            self.assertFalse(utils.test_connection())
            self.assertEqual(utils.get_auth_header(), None)
            mock_head.assert_called_with(AETHER_KERNEL_URL_TEST_MOCK)
            mock_get.assert_called_with(
                AETHER_KERNEL_URL_TEST_MOCK,
                headers={
                    'Authorization': 'Token {}'.format(AETHER_KERNEL_TOKEN_MOCK)
                },
            )

    @mock.patch.dict('os.environ', AETHER_ENV_MOCK)
    def test_submit_to_kernel__without_mapping_id(self):
        self.assertRaises(
            Exception,
            utils.submit_to_kernel,
            submission={},
            submission_fk=None,
        )

    @mock.patch.dict('os.environ', AETHER_ENV_MOCK)
    def test_submit_to_kernel__without_submission(self):
        self.assertRaises(
            Exception,
            utils.submit_to_kernel,
            submission=None,
            submission_fk=1,
        )

    @mock.patch('requests.put')
    @mock.patch('requests.post')
    @mock.patch.dict('os.environ', AETHER_ENV_MOCK)
    def test_submit_to_kernel__without_submission_id(self, mock_post, mock_put):
        utils.submit_to_kernel(submission={'_id': 'a'}, submission_fk=1, submission_id=None)
        mock_put.assert_not_called()
        mock_post.assert_called()

    @mock.patch('requests.put')
    @mock.patch('requests.post')
    @mock.patch.dict('os.environ', AETHER_ENV_MOCK)
    def test_submit_to_kernel__with_submission_id(self, mock_post, mock_put):
        utils.submit_to_kernel(submission={'_id': 'a'}, submission_fk=1, submission_id=1)
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
