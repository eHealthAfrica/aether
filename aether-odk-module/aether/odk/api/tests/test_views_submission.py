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
import requests

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status

from aether.common.kernel import utils as common_kernel_utils

from . import CustomTestCase, MockResponse
from ..views import XML_SUBMISSION_PARAM
from ..kernel_utils import propagate_kernel_artefacts, KernelPropagationError


class SubmissionTests(CustomTestCase):

    def setUp(self):
        super(SubmissionTests, self).setUp()
        self.helper_create_user()
        self.url = reverse('xform-submission')

    #
    # Test submission with authorization error on kernel server side
    #
    @mock.patch('aether.common.kernel.utils.test_connection', return_value=False)
    def test__submission__424__connection(self, mock_test):
        response = self.client.head(self.url, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_424_FAILED_DEPENDENCY)

        response = self.client.post(self.url, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_424_FAILED_DEPENDENCY)

    def test__submission__204(self):
        response = self.client.head(self.url, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test__submission__404(self):
        # submit response without xForm
        with open(self.samples['submission']['file-ok'], 'rb') as f:
            response = self.client.post(
                self.url,
                {XML_SUBMISSION_PARAM: f},
                **self.headers_user
            )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test__submission__422(self):
        # submit without xml file
        response = self.client.post(self.url, {}, **self.headers_user)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

        # submit wrong xml
        with open(self.samples['submission']['file-err'], 'rb') as f:
            response = self.client.post(
                self.url,
                {XML_SUBMISSION_PARAM: f},
                **self.headers_user
            )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test__submission__424__propagation(self):
        # with xform and right xml but not kernel propagation
        self.helper_create_xform(surveyor=self.user, xml_data=self.samples['xform']['raw-xml'])
        with mock.patch('aether.odk.api.views.propagate_kernel_artefacts',
                        side_effect=KernelPropagationError):
            with open(self.samples['submission']['file-ok'], 'rb') as f:
                response = self.client.post(
                    self.url,
                    {XML_SUBMISSION_PARAM: f},
                    **self.headers_user
                )
        self.assertEqual(response.status_code, status.HTTP_424_FAILED_DEPENDENCY)

    @mock.patch('aether.odk.api.views.propagate_kernel_artefacts', return_value=True)
    def test__submission__400(self, mock_propagate):
        # create xForm entry
        self.helper_create_xform(surveyor=self.user, xml_data=self.samples['xform']['raw-xml'])

        # submit right response but server is not available yet
        with open(self.samples['submission']['file-ok'], 'rb') as f:
            response = self.client.post(
                self.url,
                {XML_SUBMISSION_PARAM: f},
                **self.headers_user
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PostSubmissionTests(CustomTestCase):

    def setUp(self):
        super(PostSubmissionTests, self).setUp()

        self.helper_create_user()
        self.url = reverse('xform-submission')

        # create xForm entry
        self.xform = self.helper_create_xform(
            surveyor=self.user,
            xml_data=self.samples['xform']['raw-xml'],
        )
        self.assertTrue(self.xform.is_surveyor(self.user))
        self.assertIsNotNone(self.xform.kernel_id)
        # propagate in kernel
        self.assertTrue(propagate_kernel_artefacts(self.xform))

        # check Kernel testing server
        self.assertTrue(common_kernel_utils.test_connection())
        self.KERNEL_HEADERS = common_kernel_utils.get_auth_header()
        kernel_url = common_kernel_utils.get_kernel_server_url()
        self.MAPPING_URL = common_kernel_utils.get_mappings_url(self.xform.kernel_id)
        self.SUBMISSIONS_URL = common_kernel_utils.get_submissions_url()
        self.ATTACHMENTS_URL = common_kernel_utils.get_attachments_url()
        self.PROJECT_URL = f'{kernel_url}/projects/{str(self.xform.project.project_id)}/'
        self.SCHEMA_URL = f'{kernel_url}/schemas/{str(self.xform.kernel_id)}/'

    def tearDown(self):
        super(PostSubmissionTests, self).tearDown()

        # delete the test objects created in kernel testing server
        requests.delete(self.PROJECT_URL, headers=self.KERNEL_HEADERS)
        requests.delete(self.SCHEMA_URL, headers=self.KERNEL_HEADERS)

    def helper_check_submission(self, succeed=True, attachments=0):
        response = requests.get(
            self.MAPPING_URL + '?fields=submissions_url',
            headers=self.KERNEL_HEADERS,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.json()

        # get submissions
        response = requests.get(content['submissions_url'], headers=self.KERNEL_HEADERS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.json()
        self.assertEqual(content['count'], 1 if succeed else 0)

        if succeed:
            submission = content['results'][0]

            # get entities
            response = requests.get(submission['entities_url'], headers=self.KERNEL_HEADERS)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            content = response.json()
            self.assertEqual(content['count'], 1)  # using identity mapping

            # get attachments
            response = requests.get(submission['attachments_url'], headers=self.KERNEL_HEADERS)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            content = response.json()
            # there is always one more attachment, the original submission content itself
            self.assertEqual(content['count'], attachments + 1)

    def test__submission__post__no_granted_surveyor(self):
        # remove user as granted surveyor
        self.xform.project.surveyors.clear()
        self.xform.project.save()
        self.xform.surveyors.clear()
        self.xform.surveyors.add(self.helper_create_surveyor())
        self.xform.save()
        self.assertFalse(self.xform.is_surveyor(self.user))

        with open(self.samples['submission']['file-ok'], 'rb') as f:
            response = self.client.post(
                self.url,
                {XML_SUBMISSION_PARAM: f},
                **self.headers_user
            )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.helper_check_submission(succeed=False)

    @mock.patch('requests.delete')
    @mock.patch('requests.post', side_effect=Exception)
    def test__submission__post__with_unexpected_error(self, mock_post, mock_delete):
        # there is going to be an unexpected error during attachment post
        with open(self.samples['submission']['file-ok'], 'rb') as f:
            response = self.client.post(
                self.url,
                {XML_SUBMISSION_PARAM: f},
                **self.headers_user
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_post.assert_called_once_with(
            self.SUBMISSIONS_URL,
            headers=self.KERNEL_HEADERS,
            json=mock.ANY,
        )
        mock_delete.assert_not_called()
        self.helper_check_submission(succeed=False)

    @mock.patch('requests.delete')
    @mock.patch('requests.post', return_value=MockResponse(status_code=500))
    def test__submission__post__with_kernel_error(self, mock_post, mock_delete):
        with open(self.samples['submission']['file-ok'], 'rb') as f:
            response = self.client.post(
                self.url,
                {XML_SUBMISSION_PARAM: f},
                **self.headers_user
            )
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        mock_post.assert_called_once_with(
            self.SUBMISSIONS_URL,
            headers=self.KERNEL_HEADERS,
            json=mock.ANY,
        )
        mock_delete.assert_not_called()
        self.helper_check_submission(succeed=False)

    def test__submission__post(self):
        with open(self.samples['submission']['file-ok'], 'rb') as f:
            response = self.client.post(
                self.url,
                {XML_SUBMISSION_PARAM: f},
                **self.headers_user
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content.decode())
        self.helper_check_submission()

    def test__submission__post__with_attachment(self):
        # submit response with one attachment
        with open(self.samples['submission']['file-ok'], 'rb') as f:
            response = self.client.post(
                self.url,
                {
                    XML_SUBMISSION_PARAM: f,
                    'attach': SimpleUploadedFile('audio.wav', b'abc'),
                },
                **self.headers_user
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content.decode())

        # check that submission was created with one attachment
        self.helper_check_submission(attachments=1)

    def test__submission__post__with_attachments(self):
        # submit response with more than one attachment
        with open(self.samples['submission']['file-ok'], 'rb') as f:
            response = self.client.post(
                self.url,
                {
                    XML_SUBMISSION_PARAM: f,
                    'attach_1': SimpleUploadedFile('audio1.wav', b'abc'),
                    'attach_2': SimpleUploadedFile('audio2.wav', b'abc'),
                    'attach_3': SimpleUploadedFile('audio3.wav', b'abc'),
                    'attach_4': SimpleUploadedFile('audio4.wav', b'abc'),
                },
                **self.headers_user
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content.decode())

        # check that submission was created with four attachments
        self.helper_check_submission(attachments=4)

    def test__submission__post__with_attachments__multiple_requests(self):
        # An ODK Collect submission containing several large attachments will be
        # split up into several POST requests. The form data in all these
        # requests is identical, but the attachments differ. In this test, we
        # check that all attachments belonging to e.g. one ODK Collect submission
        # get associated with that submission -- even if they arrive at different
        # times.
        count = 3
        for _ in range(count):
            with open(self.samples['submission']['file-ok'], 'rb') as f:
                response = self.client.post(
                    self.url,
                    {
                        XML_SUBMISSION_PARAM: f,
                        'attach': SimpleUploadedFile('audio.wav', b'abc'),
                    },
                    **self.headers_user
                )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content.decode())
        self.helper_check_submission(attachments=count)

    def test__submission__post__no_instance_id(self):
        with open(self.samples['submission']['file-err-missing-instance-id'], 'rb') as f:
            response = self.client.post(
                self.url,
                {
                    XML_SUBMISSION_PARAM: f,
                    'attach': SimpleUploadedFile('audio.wav', b'abc'),
                },
                **self.headers_user
            )
            self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    @mock.patch('requests.delete')
    @mock.patch('requests.post',
                side_effect=[
                    MockResponse(status_code=201, json_data={'id': 'submission-id'}),
                    MockResponse(status_code=404)
                ])
    def test__submission__post__with_attachments__with_kernel_error(self, mock_post, mock_delete):
        # there is going to be an error during attachment post
        with open(self.samples['submission']['file-ok'], 'rb') as f:
            response = self.client.post(
                self.url,
                {
                    XML_SUBMISSION_PARAM: f,
                    'attach': SimpleUploadedFile('audio.wav', b'abc'),
                },
                **self.headers_user
            )
        mock_post.assert_any_call(
            self.SUBMISSIONS_URL,
            headers=self.KERNEL_HEADERS,
            json=mock.ANY,
        )
        mock_post.assert_any_call(
            self.ATTACHMENTS_URL,
            headers=self.KERNEL_HEADERS,
            data={'submission': 'submission-id'},
            files=mock.ANY,
        )
        mock_delete.assert_called_once()

        self.assertEqual(response.status_code, 404, 'returns the last status code')
        self.helper_check_submission(succeed=False)

    @mock.patch('requests.delete')
    @mock.patch('requests.post',
                side_effect=[
                    MockResponse(status_code=201, json_data={'id': 'submission-id'}),
                    Exception
                ])
    def test__submission__post__with_attachments__with_unexpected_error(self, mock_post, mock_del):
        # there is going to be an unexpected error during attachment post
        with open(self.samples['submission']['file-ok'], 'rb') as f:
            response = self.client.post(
                self.url,
                {
                    XML_SUBMISSION_PARAM: f,
                    'attach': SimpleUploadedFile('audio.wav', b'abc'),
                },
                **self.headers_user
            )
        mock_post.assert_any_call(
            self.SUBMISSIONS_URL,
            headers=self.KERNEL_HEADERS,
            json=mock.ANY,
        )
        mock_post.assert_any_call(
            self.ATTACHMENTS_URL,
            headers=self.KERNEL_HEADERS,
            data={'submission': 'submission-id'},
            files=mock.ANY,
        )
        mock_del.assert_called_once()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content.decode())
        self.helper_check_submission(succeed=False)
