# Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
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

import json
from unittest import mock
import requests

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, override_settings
from django.urls import reverse

from rest_framework import status

from aether.sdk.unittest import MockResponse

from ...tests import CustomTestCase
from ... import kernel_utils
from ...surveyors_utils import is_granted_surveyor

from ..views import XML_SUBMISSION_PARAM


@override_settings(MULTITENANCY=False)
class SubmissionTests(CustomTestCase):

    def setUp(self):
        super(SubmissionTests, self).setUp()
        self.surveyor = self.helper_create_surveyor()
        self.url = reverse('xform-submission')

    @mock.patch('aether.odk.api.collect.views.check_kernel_connection', return_value=False)
    def test__submission__424__connection(self, *args):
        # Test submission with authorization error on kernel server side
        response = self.client.head(self.url, **self.headers_surveyor)
        self.assertEqual(response.status_code, status.HTTP_424_FAILED_DEPENDENCY, response.content)

        response = self.client.post(self.url, **self.headers_surveyor)
        self.assertEqual(response.status_code, status.HTTP_424_FAILED_DEPENDENCY, response.content)

    def test__submission__204(self):
        response = self.client.head(self.url, **self.headers_surveyor)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response['X-OpenRosa-Version'], '1.0')

    def test__submission__404(self):
        # submit response without xForm
        with open(self.samples['submission']['file-ok'], 'rb') as f:
            response = self.client.post(self.url, {XML_SUBMISSION_PARAM: f}, **self.headers_surveyor)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test__submission__422(self):
        # submit without xml file
        response = self.client.post(self.url, {}, **self.headers_surveyor)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY, response.content)

        # submit wrong xml
        with open(self.samples['submission']['file-err'], 'rb') as f:
            response = self.client.post(self.url, {XML_SUBMISSION_PARAM: f}, **self.headers_surveyor)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY, response.content)

    @mock.patch('aether.odk.api.collect.views.check_kernel_connection', return_value=True)
    @mock.patch('aether.odk.api.collect.views.propagate_kernel_artefacts',
                side_effect=kernel_utils.KernelPropagationError)
    def test__submission__424__propagation(self, *args):
        # with xform and right xml but not kernel propagation
        self.helper_create_xform(surveyor=self.surveyor, xml_data=self.samples['xform']['raw-xml'])
        with open(self.samples['submission']['file-ok'], 'rb') as f:
            response = self.client.post(self.url, {XML_SUBMISSION_PARAM: f}, **self.headers_surveyor)
        self.assertEqual(response.status_code, status.HTTP_424_FAILED_DEPENDENCY, response.content)


@override_settings(MULTITENANCY=False)
class PostSubmissionTests(CustomTestCase):

    def setUp(self):
        super(PostSubmissionTests, self).setUp()

        self.surveyor = self.helper_create_surveyor()
        self.request = RequestFactory().get('/')
        self.request.user = self.surveyor

        self.url = reverse('xform-submission')

        # create xForm entry
        self.xform = self.helper_create_xform(
            surveyor=self.surveyor,
            xml_data=self.samples['xform']['raw-xml'],
        )
        self.assertTrue(is_granted_surveyor(self.request, self.xform))
        self.assertIsNotNone(self.xform.kernel_id)
        # propagate in kernel
        self.assertTrue(kernel_utils.propagate_kernel_artefacts(self.xform))

        # check Kernel testing server
        self.assertTrue(kernel_utils.check_kernel_connection())
        self.KERNEL_HEADERS = kernel_utils.get_kernel_auth_header()
        self.KERNEL_URL = kernel_utils.get_kernel_url()
        self.MAPPINGSET_URL = f'{self.KERNEL_URL}/mappingsets/{str(self.xform.kernel_id)}/'
        self.SUBMISSIONS_URL = kernel_utils.get_submissions_url()
        self.ATTACHMENTS_URL = kernel_utils.get_attachments_url()
        self.ENTITIES_URL = f'{self.KERNEL_URL}/entities/?page_size=1'
        # cleaning the house
        self.PROJECT_URL = f'{self.KERNEL_URL}/projects/{str(self.xform.project.project_id)}/'
        self.SCHEMA_URL = f'{self.KERNEL_URL}/schemas/{str(self.xform.kernel_id)}/'

        # Check the current entities (there should be none)
        response = requests.get(self.ENTITIES_URL, headers=self.KERNEL_HEADERS)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        self.ENTITIES_COUNT = response.json()['count']

    def tearDown(self):
        super(PostSubmissionTests, self).tearDown()

        # delete the test objects created in kernel testing server
        requests.delete(self.PROJECT_URL, headers=self.KERNEL_HEADERS)
        requests.delete(self.SCHEMA_URL, headers=self.KERNEL_HEADERS)

    def helper_check_submission(self, succeed=True, attachments=0, entity=None):
        response = requests.get(
            self.MAPPINGSET_URL + '?fields=submissions_url',
            headers=self.KERNEL_HEADERS,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        content = response.json()

        # get submissions
        response = requests.get(content['submissions_url'], headers=self.KERNEL_HEADERS)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        content = response.json()
        self.assertEqual(content['count'], 1 if succeed else 0)

        if succeed:
            submission = content['results'][0]

            # get entities
            response = requests.get(submission['entities_url'], headers=self.KERNEL_HEADERS)
            self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
            content = response.json()
            self.assertEqual(content['count'], 1)  # using identity mapping
            if entity:  # check that the entity payload matches
                payload = dict(content['results'][0]['payload'])
                # remove added fields
                for f in ['id', '_submitted_at']:
                    self.assertIn(f, payload)
                    del payload[f]
                # special case with _surveyor
                self.assertIn('_surveyor', payload)
                self.assertEqual(payload['_surveyor'], self.surveyor.username)
                del payload['_surveyor']

                self.assertEqual(payload, entity)

            # get attachments
            response = requests.get(submission['attachments_url'], headers=self.KERNEL_HEADERS)
            self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
            content = response.json()
            # there is always one more attachment, the original submission content itself
            self.assertEqual(content['count'], attachments + 1)

        else:
            # there are no new entities
            response = requests.get(self.ENTITIES_URL, headers=self.KERNEL_HEADERS)
            self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
            content = response.json()
            self.assertEqual(content['count'], self.ENTITIES_COUNT)

    def test__submission__post__no_granted_surveyor(self):
        # remove user as granted surveyor
        self.xform.project.surveyors.clear()
        self.xform.surveyors.clear()
        self.xform.surveyors.add(self.helper_create_surveyor('surveyor2'))
        self.assertFalse(is_granted_surveyor(self.request, self.xform))

        with open(self.samples['submission']['file-ok'], 'rb') as f:
            response = self.client.post(self.url, {XML_SUBMISSION_PARAM: f}, **self.headers_surveyor)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, response.content)
        self.helper_check_submission(succeed=False)

    def test__submission__post__no_instance_id(self):
        with open(self.samples['submission']['file-err-missing-instance-id'], 'rb') as f:
            response = self.client.post(self.url, {XML_SUBMISSION_PARAM: f}, **self.headers_surveyor)
            self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY, response.content)

    @mock.patch('aether.odk.api.collect.views.exec_request', side_effect=Exception)
    def test__submission__post__with_error_on_check_previous_submission(self, mock_req):
        with open(self.samples['submission']['file-ok'], 'rb') as f:
            response = self.client.post(self.url, {XML_SUBMISSION_PARAM: f}, **self.headers_surveyor)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

        mock_req.assert_called_once_with(
            method='get',
            url=self.SUBMISSIONS_URL,
            headers=self.KERNEL_HEADERS,
            params={'payload__meta__instanceID': mock.ANY},
        )

    def test__submission__post__not_201(self, *args):
        def my_side_effect(*args, **kwargs):
            if kwargs['method'] != 'post':
                # real method
                return requests.request(*args, **kwargs)
            else:
                # there is going to be an unexpected response during submission post
                return MockResponse(status_code=204)

        with mock.patch('aether.odk.api.collect.views.exec_request',
                        side_effect=my_side_effect) as mock_req:
            with open(self.samples['submission']['file-ok'], 'rb') as f:
                response = self.client.post(self.url, {XML_SUBMISSION_PARAM: f}, **self.headers_surveyor)
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)
            mock_req.assert_has_calls([
                mock.call(
                    method='get',
                    url=self.SUBMISSIONS_URL,
                    headers=self.KERNEL_HEADERS,
                    params={'payload__meta__instanceID': mock.ANY},
                ),
                mock.call(
                    method='post',
                    url=self.SUBMISSIONS_URL,
                    headers=self.KERNEL_HEADERS,
                    json={'payload': mock.ANY, 'mappingset': str(self.xform.kernel_id)},
                ),
            ])

    def test__submission__post__with_unexpected_error(self):
        def my_side_effect(*args, **kwargs):
            if kwargs['url'] != self.ATTACHMENTS_URL:
                # real method
                return requests.request(*args, **kwargs)
            else:
                # there is going to be an unexpected error during attachment post
                raise Exception

        with mock.patch('aether.odk.api.collect.views.exec_request', side_effect=my_side_effect) as mock_req:
            with open(self.samples['submission']['file-ok'], 'rb') as f:
                response = self.client.post(self.url, {XML_SUBMISSION_PARAM: f}, **self.headers_surveyor)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)
            mock_req.assert_has_calls([
                mock.call(
                    method='get',
                    url=self.SUBMISSIONS_URL,
                    headers=self.KERNEL_HEADERS,
                    params={'payload__meta__instanceID': mock.ANY},
                ),
                mock.call(
                    method='post',
                    url=self.SUBMISSIONS_URL,
                    headers=self.KERNEL_HEADERS,
                    json={'payload': mock.ANY, 'mappingset': str(self.xform.kernel_id)},
                ),
                mock.call(
                    method='post',
                    url=self.ATTACHMENTS_URL,
                    headers=self.KERNEL_HEADERS,
                    data=mock.ANY,
                    files=mock.ANY,
                ),
                mock.call(
                    method='delete',
                    url=mock.ANY,
                    headers=mock.ANY,
                    params={'cascade': 'true'},
                ),
            ])

        self.helper_check_submission(succeed=False)

    def test__submission__post__with_kernel_error(self):
        def my_side_effect(*args, **kwargs):
            if kwargs['url'] != self.ATTACHMENTS_URL:
                # real method
                return requests.request(*args, **kwargs)
            else:
                return MockResponse(status_code=500)

        with mock.patch('aether.odk.api.collect.views.exec_request', side_effect=my_side_effect) as mock_req:
            with open(self.samples['submission']['file-ok'], 'rb') as f:
                response = self.client.post(self.url, {XML_SUBMISSION_PARAM: f}, **self.headers_surveyor)
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR, response.content)
            mock_req.assert_has_calls([
                mock.call(
                    method='get',
                    url=self.SUBMISSIONS_URL,
                    headers=self.KERNEL_HEADERS,
                    params={'payload__meta__instanceID': mock.ANY},
                ),
                mock.call(
                    method='post',
                    url=self.SUBMISSIONS_URL,
                    headers=self.KERNEL_HEADERS,
                    json={'payload': mock.ANY, 'mappingset': str(self.xform.kernel_id)},
                ),
                mock.call(
                    method='post',
                    url=self.ATTACHMENTS_URL,
                    headers=self.KERNEL_HEADERS,
                    data=mock.ANY,
                    files=mock.ANY,
                ),
                mock.call(
                    method='delete',
                    url=mock.ANY,
                    headers=mock.ANY,
                    params={'cascade': 'true'},
                ),
            ])

        self.helper_check_submission(succeed=False)

    def test__submission__post(self):
        with open(self.samples['submission']['file-ok-json'], 'rb') as content:
            entity_payload = dict(json.load(content))
            del entity_payload['not_in_the_definition']  # not in the AVRO schema

        with open(self.samples['submission']['file-ok'], 'rb') as f:
            response = self.client.post(self.url, {XML_SUBMISSION_PARAM: f}, **self.headers_surveyor)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        self.helper_check_submission(entity=entity_payload)

    def test__submission__post__with_one_attachment(self):
        with open(self.samples['submission']['file-ok-json'], 'rb') as content:
            entity_payload = dict(json.load(content))
            del entity_payload['not_in_the_definition']  # not in the AVRO schema

        # submit response with one attachment
        with open(self.samples['submission']['file-ok'], 'rb') as f:
            response = self.client.post(
                self.url,
                {
                    XML_SUBMISSION_PARAM: f,
                    'attach': SimpleUploadedFile('audio.wav', b'abc'),
                },
                **self.headers_surveyor
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        # check that submission was created with one attachment
        self.helper_check_submission(attachments=1)

    def test__submission__post__with_attachments__in_one_request(self):
        with open(self.samples['submission']['file-ok-json'], 'rb') as content:
            entity_payload = dict(json.load(content))
            del entity_payload['not_in_the_definition']  # not in the AVRO schema

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
                **self.headers_surveyor
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        # check that submission was created with four attachments
        self.helper_check_submission(entity=entity_payload, attachments=4)

    def test__submission__post__with_attachments__in_multiple_requests(self):
        with open(self.samples['submission']['file-ok-json'], 'rb') as content:
            entity_payload = dict(json.load(content))
            del entity_payload['not_in_the_definition']  # not in the AVRO schema

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
                    **self.headers_surveyor
                )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        self.helper_check_submission(entity=entity_payload, attachments=count)

    def test__submission__post__with_attachments__with_kernel_error(self):
        def my_side_effect(*args, **kwargs):
            if kwargs['url'] != self.ATTACHMENTS_URL:
                # real method
                return requests.request(*args, **kwargs)
            else:
                if kwargs['files']['attachment_file'][0] != 'audio.wav':
                    return MockResponse(status_code=201)
                else:
                    return MockResponse(status_code=404)

        with mock.patch('aether.odk.api.collect.views.exec_request', side_effect=my_side_effect) as mock_req:
            # there is going to be an error during second attachment post
            with open(self.samples['submission']['file-ok'], 'rb') as f:
                response = self.client.post(
                    self.url,
                    {
                        XML_SUBMISSION_PARAM: f,
                        'attach': SimpleUploadedFile('audio.wav', b'abc'),
                    },
                    **self.headers_surveyor
                )
            self.assertEqual(response.status_code, 404, 'returns the last status code')
            mock_req.assert_has_calls([
                mock.call(
                    method='get',
                    url=self.SUBMISSIONS_URL,
                    headers=self.KERNEL_HEADERS,
                    params={'payload__meta__instanceID': mock.ANY},
                ),
                # submission
                mock.call(
                    method='post',
                    url=self.SUBMISSIONS_URL,
                    headers=self.KERNEL_HEADERS,
                    json={'payload': mock.ANY, 'mappingset': str(self.xform.kernel_id)},
                ),
                # 1st attachment
                mock.call(
                    method='post',
                    url=self.ATTACHMENTS_URL,
                    headers=self.KERNEL_HEADERS,
                    data=mock.ANY,
                    files=mock.ANY,
                ),
                # 2nd attachment (with 404 response)
                mock.call(
                    method='post',
                    url=self.ATTACHMENTS_URL,
                    headers=self.KERNEL_HEADERS,
                    data=mock.ANY,
                    files=mock.ANY,
                ),
                mock.call(
                    method='delete',
                    url=mock.ANY,
                    headers=mock.ANY,
                    params={'cascade': 'true'},
                ),
            ])

        self.helper_check_submission(succeed=False)

    def test__submission__post__with_attachments__with_unexpected_error(self):
        def my_side_effect(*args, **kwargs):
            if kwargs['url'] != self.ATTACHMENTS_URL:
                # real method
                return requests.request(*args, **kwargs)
            else:
                if kwargs['files']['attachment_file'][0] != 'audio.wav':
                    return MockResponse(status_code=201)
                else:
                    raise Exception

        with mock.patch('aether.odk.api.collect.views.exec_request', side_effect=my_side_effect) as mock_req:
            # there is going to be an error during second attachment post
            with open(self.samples['submission']['file-ok'], 'rb') as f:
                response = self.client.post(
                    self.url,
                    {
                        XML_SUBMISSION_PARAM: f,
                        'attach': SimpleUploadedFile('audio.wav', b'abc'),
                    },
                    **self.headers_surveyor
                )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)
            mock_req.assert_has_calls([
                mock.call(
                    method='get',
                    url=self.SUBMISSIONS_URL,
                    headers=self.KERNEL_HEADERS,
                    params={'payload__meta__instanceID': mock.ANY},
                ),
                # submission
                mock.call(
                    method='post',
                    url=self.SUBMISSIONS_URL,
                    headers=self.KERNEL_HEADERS,
                    json={'payload': mock.ANY, 'mappingset': str(self.xform.kernel_id)},
                ),
                # 1st attachment
                mock.call(
                    method='post',
                    url=self.ATTACHMENTS_URL,
                    headers=self.KERNEL_HEADERS,
                    data=mock.ANY,
                    files=mock.ANY,
                ),
                # 2nd attachment (raises exception)
                mock.call(
                    method='post',
                    url=self.ATTACHMENTS_URL,
                    headers=self.KERNEL_HEADERS,
                    data=mock.ANY,
                    files=mock.ANY,
                ),
                mock.call(
                    method='delete',
                    url=mock.ANY,
                    headers=mock.ANY,
                    params={'cascade': 'true'},
                ),
            ])

        self.helper_check_submission(succeed=False)
