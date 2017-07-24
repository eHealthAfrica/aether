import base64
import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status

XLS_FILE = '/code/api/tests/demo-xlsform.xls'
XML_FILE = '/code/api/tests/demo-xlsform.xml'
XML_ERR_FILE = '/code/api/tests/demo-xlsform--error.xml'

GATHER_CORE_URL_MOCK = 'http://mock-core:8000'
GATHER_CORE_TOKEN_MOCK = 'mock-valid-token'
GATHER_ENV_MOCK = {
    'GATHER_CORE_URL': GATHER_CORE_URL_MOCK,
    'GATHER_CORE_TOKEN': GATHER_CORE_TOKEN_MOCK,
}
GATHER_HEADER_MOCK = {'Authorization': 'Token {}'.format(GATHER_CORE_TOKEN_MOCK)}

SURVEY_URL = '{}/surveys/1/responses/'.format(GATHER_CORE_URL_MOCK)
ATTACHMENT_URL = '{}/responses/2/attachments'.format(GATHER_CORE_URL_MOCK)


class CustomTestCase(TestCase):

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

        # mock test connection (pass authorization)
        patcherTC = mock.patch('api.core_utils.test_connection', return_value=True)
        patcherTC.start()
        self.addCleanup(patcherTC.stop)

        # mock gather env variables
        patcherEnv = mock.patch.dict('os.environ', GATHER_ENV_MOCK)
        patcherEnv.start()
        self.addCleanup(patcherEnv.stop)

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
                {'xlsform': f, 'description': 'some text', 'gather_core_survey_id': 1},
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

        # create xForm entry
        with open(XLS_FILE, 'rb') as f:
            self.client.post(
                reverse('admin:api_xform_add'),
                {
                    'xlsform': f,
                    'description': 'some text',
                    'gather_core_survey_id': 1,
                },
            )

    #
    # Test submission with error on core server side
    #
    def test__submission__post__with_core_error(self):
        with mock.patch(
            'requests.post',
            return_value=mock.Mock(status_code=500)
        ) as mock_post:
            with open(XML_FILE, 'rb') as f:
                response = self.client.post(
                    reverse('submission'),
                    {'xml_submission_file': f},
                    **self.headers
                )
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            mock_post.assert_called_once_with(
                SURVEY_URL,
                headers=GATHER_HEADER_MOCK,
                json=mock.ANY,
            )

    #
    # Test submission without error on core server side
    #
    def test__submission__post(self):
        with mock.patch(
            'requests.post',
            return_value=mock.Mock(
                status_code=201,
                content={'attachments_url': ATTACHMENT_URL},
            )
        ) as mock_post:
            with open(XML_FILE, 'rb') as f:
                response = self.client.post(
                    reverse('submission'),
                    {'xml_submission_file': f},
                    **self.headers
                )

            mock_post.assert_called_with(
                SURVEY_URL,
                headers=GATHER_HEADER_MOCK,
                json=mock.ANY,
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    #
    # Test submission with attachments
    #
    def test__submission__post__with_attachments(self):
        with mock.patch(
            'requests.post',
            return_value=mock.Mock(
                status_code=201,
                content={'attachments_url': ATTACHMENT_URL},
            )
        ) as mock_post:
            # submit response with itself as attachment
            with open(XML_FILE, 'rb') as f:
                with open(XML_FILE, 'rb') as f2:
                    response = self.client.post(
                        reverse('submission'),
                        {'xml_submission_file': f, 'attach': f2},
                        **self.headers
                    )

            mock_post.assert_called_with(
                mock.ANY,
                headers=GATHER_HEADER_MOCK,
                data={'name': 'attach'},
                files=mock.ANY,
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
