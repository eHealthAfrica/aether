import base64
import mock
import requests

from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from django.urls import reverse

from rest_framework import status
from api import core_utils

XLS_FILE = '/code/api/tests/demo-xlsform.xls'
XML_FILE = '/code/api/tests/demo-xlsform.xml'
XML_ERR_FILE = '/code/api/tests/demo-xlsform--error.xml'

GATHER_CORE_URL_TESTING = core_utils.get_core_server_url()
GATHER_HEADER_TESTING = core_utils.get_auth_header()


class CustomTestCase(TransactionTestCase):

    def setUp(self):
        username = 'test'
        email = 'test@example.com'
        password = 'testtest'
        basic = b'test:testtest'
        get_user_model().objects.create_superuser(username, email, password)

        self.assertTrue(self.client.login(username=username, password=password))
        self.headers = {
            'HTTP_AUTHORIZATION': 'Basic ' + base64.b64encode(basic).decode('ascii')
        }

    def tearDown(self):
        self.client.logout()


class SubmissionTests(CustomTestCase):

    #
    # Test submission with authorization error on core server side
    #
    @mock.patch('api.core_utils.test_connection', return_value=False)
    def test__submission__503(self, mock_test):
        response = self.client.head(reverse('submission'), **self.headers)
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

        response = self.client.post(reverse('submission'), **self.headers)
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test__submission__204(self):
        response = self.client.head(reverse('submission'), **self.headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test__submission__404(self):
        # submit response without xForm
        with open(XML_FILE, 'rb') as f:
            response = self.client.post(
                reverse('submission'),
                {'xml_submission_file': f},
                **self.headers
            )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test__submission__422(self):
        # submit without xml file
        with open(XML_FILE, 'rb') as f:
            response = self.client.post(
                reverse('submission'),
                {'xml_submission_file': ''},
                **self.headers
            )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        # submit wrong xml
        with open(XML_ERR_FILE, 'rb') as f:
            response = self.client.post(
                reverse('submission'),
                {'xml_submission_file': f},
                **self.headers
            )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test__submission__400(self):
        # create xForm entry
        with open(XLS_FILE, 'rb') as f:
            self.client.post(
                reverse('admin:api_xform_add'),
                {'xlsform': f, 'description': 'some text', 'gather_core_survey_id': 99},
            )
        # submit right response but server is not available yet
        with open(XML_FILE, 'rb') as f:
            response = self.client.post(
                reverse('submission'),
                {'xml_submission_file': f},
                **self.headers
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PostSubmissionTests(CustomTestCase):

    def setUp(self):
        super(PostSubmissionTests, self).setUp()

        # create survey in Core testing server
        testing_survey = {
            "name": "testing",
            "schema": {}
        }

        self.assertTrue(core_utils.test_connection())
        # create survey in core testing server
        response = requests.post(core_utils.get_surveys_url(),
                                 json=testing_survey,
                                 headers=GATHER_HEADER_TESTING)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        survey_id = data['id']
        self.SURVEY_URL = core_utils.get_surveys_url(survey_id)
        self.RESPONSES_URL = core_utils.get_survey_responses_url(survey_id)

        # create xForm entry
        with open(XLS_FILE, 'rb') as f:
            response = self.client.post(
                reverse('admin:api_xform_add'),
                {
                    'xlsform': f,
                    'description': 'some text',
                    'gather_core_survey_id': survey_id,
                },
            )
        self.assertFalse(status.is_server_error(response.status_code))

    def tearDown(self):
        super().tearDown()
        # delete ALL surveys in core testing server
        requests.delete(self.SURVEY_URL, headers=GATHER_HEADER_TESTING)

    @mock.patch('requests.post', return_value=mock.Mock(status_code=500))
    def test__submission__post__with_core_error(self, mock_post):
        with open(XML_FILE, 'rb') as f:
            response = self.client.post(
                reverse('submission'),
                {'xml_submission_file': f},
                **self.headers
            )
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        mock_post.assert_called_once_with(
            self.RESPONSES_URL,
            headers=GATHER_HEADER_TESTING,
            json=mock.ANY,
        )

    def test__submission__post(self):
        with open(XML_FILE, 'rb') as f:
            response = self.client.post(
                reverse('submission'),
                {'xml_submission_file': f},
                **self.headers
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test__submission__post__with_attachments(self):
        # submit response with itself as attachment
        with open(XML_FILE, 'rb') as f:
            with open(XML_FILE, 'rb') as f2:
                response = self.client.post(
                    reverse('submission'),
                    {'xml_submission_file': f, 'attach': f2},
                    **self.headers
                )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @mock.patch('requests.post', side_effect=[mock.DEFAULT, mock.Mock(status_code=500)])
    def test__submission__post__with_attachments_error_400(self, mock_post):
        # there is going to be an error during attachment post
        with open(XML_FILE, 'rb') as f:
            with open(XML_FILE, 'rb') as f2:
                response = self.client.post(
                    reverse('submission'),
                    {'xml_submission_file': f, 'attach': f2},
                    **self.headers
                )
        mock_post.assert_called_once_with(
            self.RESPONSES_URL,
            headers=GATHER_HEADER_TESTING,
            json=mock.ANY,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
