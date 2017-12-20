import mock
import requests

from django.urls import reverse
from rest_framework import status

from . import CustomTestCase
from aether.common.kernel import utils as kernel_utils


class SubmissionTests(CustomTestCase):

    def setUp(self):
        super(SubmissionTests, self).setUp()
        self.helper_create_user()
        self.url = reverse('xform-submission')

    #
    # Test submission with authorization error on kernel server side
    #
    @mock.patch('aether.common.kernel.utils.test_connection', return_value=False)
    def test__submission__424(self, mock_test):
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
                {'xml_submission_file': f},
                **self.headers_user
            )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test__submission__422(self):
        # submit without xml file
        with open(self.samples['submission']['file-ok'], 'rb') as f:
            response = self.client.post(
                self.url,
                {'xml_submission_file': ''},
                **self.headers_user
            )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        # submit wrong xml
        with open(self.samples['submission']['file-err'], 'rb') as f:
            response = self.client.post(
                self.url,
                {'xml_submission_file': f},
                **self.headers_user
            )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)


class PostSubmissionTests(CustomTestCase):

    def setUp(self):
        """
        Set up a basic Aether project. This assumes that the fixture in
        `/aether-kernel/aether/kernel/api/tests/fixtures/project_empty_schame.json`
        has been loaded into the kernel database. See `/scripts/test_all.sh` for
        details.
        """
        super(PostSubmissionTests, self).setUp()
        self.helper_create_user()
        self.url = reverse('xform-submission')

        # create survey in Kernel testing server
        self.assertTrue(kernel_utils.test_connection())
        self.KERNEL_HEADERS = kernel_utils.get_auth_header()
        project = requests.get(
            'http://kernel-test:9000/projects/',
            headers=self.KERNEL_HEADERS,
        ).json()['results'][0]
        projectschema = requests.get(
            'http://kernel-test:9000/projectschemas/',
            headers=self.KERNEL_HEADERS,
        ).json()['results'][0]
        testing_survey = {
            'name': 'example',
            'revision': 1,
            'project': project['id'],
            'definition': {
                "mapping": [
                    [
                        "#!uuid",
                        "Person.id"
                    ],
                    [
                        "firstname",
                        "Person.firstName"
                    ],
                    [
                        "lastname",
                        "Person.familyName"
                    ]
                ],
                "entities": {
                    "Person": projectschema['id']
                }
            }
        }
        # create survey in kernel testing server
        response = requests.post(kernel_utils.get_mappings_url(),
                                 json=testing_survey,
                                 headers=self.KERNEL_HEADERS)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())
        data = response.json()
        mapping_id = data['id']
        self.MAPPING_URL = kernel_utils.get_mappings_url(mapping_id)
        self.SUBMISSIONS_URL = kernel_utils.get_submissions_url()
        # create xForm entry
        self.xform = self.helper_create_xform(surveyor=self.user, mapping_id=mapping_id)
        self.assertTrue(self.xform.is_surveyor(self.user))

    def tearDown(self):
        super(PostSubmissionTests, self).tearDown()
        # delete ALL surveys in kernel testing server
        requests.delete(self.MAPPING_URL, headers=self.KERNEL_HEADERS)

    @mock.patch('requests.post', return_value=mock.Mock(status_code=500))
    def test__submission__post__with_kernel_error(self, mock_post):
        with open(self.samples['submission']['file-ok'], 'rb') as f:
            response = self.client.post(
                self.url,
                {'xml_submission_file': f},
                **self.headers_user
            )
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        mock_post.assert_called_once_with(
            self.SUBMISSIONS_URL,
            headers=self.KERNEL_HEADERS,
            json=mock.ANY,
        )

    def test__submission__post__no_granted_surveyor(self):
        # remove user as granted surveyor
        self.xform.survey.surveyors.clear()
        self.xform.survey.save()
        self.xform.surveyors.clear()
        self.xform.surveyors.add(self.helper_create_surveyor())
        self.xform.save()
        self.assertFalse(self.xform.is_surveyor(self.user))

        with open(self.samples['submission']['file-ok'], 'rb') as f:
            response = self.client.post(
                self.url,
                {'xml_submission_file': f},
                **self.headers_user
            )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test__submission__post(self):
        with open(self.samples['submission']['file-ok'], 'rb') as f:
            response = self.client.post(
                self.url,
                {'xml_submission_file': f},
                **self.headers_user
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # FIXME: The Attachment model used in Aether is absent from
    # Aether -- once bring that back, we can uncomment this test.
    # def test__submission__post__with_attachments(self):
    #     # submit response with itself as attachment
    #     with open(self.samples['submission']['file-ok'], 'rb') as f:
    #         with open(self.samples['submission']['file-ok'], 'rb') as f2:
    #             response = self.client.post(
    #                 self.url,
    #                 {'xml_submission_file': f, 'attach': f2},
    #                 **self.headers_user
    #             )
    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # FIXME: The Attachment model used in Aether is absent from
    # Aether -- once bring that back, we can uncomment this test.
    # @mock.patch('requests.post', side_effect=[mock.DEFAULT, mock.Mock(status_code=500)])
    # def test__submission__post__with_attachments_error_400(self, mock_post):
    #     # there is going to be an error during attachment post
    #     with open(self.samples['submission']['file-ok'], 'rb') as f:
    #         with open(self.samples['submission']['file-ok'], 'rb') as f2:
    #             response = self.client.post(
    #                 self.url,
    #                 {'xml_submission_file': f, 'attach': f2},
    #                 **self.headers_user
    #             )
    #     mock_post.assert_called_once_with(
    #         self.SUBMISSIONS_URL,
    #         headers=self.KERNEL_HEADERS,
    #         json=mock.ANY,
    #     )
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
