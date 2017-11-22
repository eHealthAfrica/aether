import mock
import requests

from django.urls import reverse
from rest_framework import status

from . import CustomTestCase
from gather2.common.core import utils as core_utils


class SubmissionTests(CustomTestCase):

    def setUp(self):
        super(SubmissionTests, self).setUp()
        self.helper_create_user()
        self.url = reverse('xform-submission')

    #
    # Test submission with authorization error on core server side
    #
    @mock.patch('gather2.common.core.utils.test_connection', return_value=False)
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
        `/gather2-core/gather2/core/api/tests/fixtures/project_empty_schame.json`
        has been loaded into the core database. See `/scripts/test_all.sh` for
        details.
        """
        super(PostSubmissionTests, self).setUp()
        self.helper_create_user()
        self.url = reverse('xform-submission')

        # create survey in Core testing server
        self.assertTrue(core_utils.test_connection())
        self.CORE_HEADERS = core_utils.get_auth_header()
        project = requests.get(
            'http://core-test:9000/projects/demo/',
            headers=self.CORE_HEADERS,
        ).json()
        projectschema = requests.get(
            'http://core-test:9000/projectschemas/Person/',
            headers=self.CORE_HEADERS,
        ).json()
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
        # create survey in core testing server
        response = requests.post(core_utils.get_surveys_url(),
                                 json=testing_survey,
                                 headers=self.CORE_HEADERS)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())
        data = response.json()
        mapping_id = data['id']
        self.SURVEY_URL = core_utils.get_surveys_url(mapping_id)
        self.RESPONSES_URL = core_utils.get_survey_responses_url(mapping_id)
        # create xForm entry
        self.xform = self.helper_create_xform(surveyor=self.user, mapping_id=mapping_id)
        self.assertTrue(self.xform.is_surveyor(self.user))

    def tearDown(self):
        super(PostSubmissionTests, self).tearDown()
        # delete ALL surveys in core testing server
        requests.delete(self.SURVEY_URL, headers=self.CORE_HEADERS)

    @mock.patch('requests.post', return_value=mock.Mock(status_code=500))
    def test__submission__post__with_core_error(self, mock_post):
        with open(self.samples['submission']['file-ok'], 'rb') as f:
            response = self.client.post(
                self.url,
                {'xml_submission_file': f},
                **self.headers_user
            )
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        mock_post.assert_called_once_with(
            self.RESPONSES_URL,
            headers=self.CORE_HEADERS,
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

    # FIXME: The Attachment model used in Gather2 is absent from
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

    # FIXME: The Attachment model used in Gather2 is absent from
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
    #         self.RESPONSES_URL,
    #         headers=self.CORE_HEADERS,
    #         json=mock.ANY,
    #     )
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
