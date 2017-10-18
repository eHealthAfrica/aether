from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TransactionTestCase

from . import EXAMPLE_SCHEMA
from ..serializers import SurveySerializer, ResponseSerializer


class SerializersTests(TransactionTestCase):

    def setUp(self):
        username = 'test'
        email = 'test@example.com'
        password = 'testtest'

        self.request = RequestFactory().get('/')
        self.request.user = get_user_model().objects.create_user(username, email, password)

    def test_survey_serializer__missing_name(self):
        survey = SurveySerializer(
            data={
                # missing 'name': 'a name',
                'schema': {},
            },
            context={'request': self.request}
        )
        self.assertFalse(survey.is_valid())

    def test_survey_serializer__wrong_schema(self):
        survey = SurveySerializer(
            data={
                'name': 'a name',
                'schema': '{ "something wrong" }',  # wrong schema
            },
            context={'request': self.request}
        )
        self.assertFalse(survey.is_valid())

    def test_survey_serializer__empty_schema(self):
        survey = SurveySerializer(
            data={
                'name': 'a name',
                'schema': '{}',
            },
            context={'request': self.request}
        )
        self.assertTrue(survey.is_valid())

    def test_survey_serializer__with_schema(self):
        survey = SurveySerializer(
            data={
                'name': 'a name',
                'schema': {
                    "a": 1,
                    "b": "2",
                    "c": [1, 2, 3],
                    "d": {
                        "e": False,
                        "f": True
                    },
                    "g": [
                        {
                            "h": {}
                        }
                    ]
                },
            },
            context={'request': self.request}
        )
        self.assertTrue(survey.is_valid())

    def test_survey_serializer__with_schema_file__empty(self):
        with open('/code/core/tests/files/empty_schema.json', 'rb') as data:
            content = SimpleUploadedFile('schema.json', data.read())

        survey = SurveySerializer(
            data={
                'name': 'a name',
                'schema_file': content,
            },
            context={'request': self.request}
        )
        self.assertTrue(survey.is_valid())

    def test_survey_serializer__with_schema_file__err(self):
        with open('/code/core/tests/files/err_schema.json', 'rb') as data:
            content = SimpleUploadedFile('schema.json', data.read())

        survey = SurveySerializer(
            data={
                'name': 'a name',
                'schema_file': content,
            },
            context={'request': self.request}
        )
        self.assertFalse(survey.is_valid())

    def test_survey_serializer__with_schema_file__with_content(self):
        with open('/code/core/tests/files/sample_schema.json', 'rb') as data:
            content = SimpleUploadedFile('schema.json', data.read())

        survey = SurveySerializer(
            data={
                'name': 'a name',
                'schema_file': content,
            },
            context={'request': self.request}
        )
        self.assertTrue(survey.is_valid())

    def test_response_serializer(self):
        survey = SurveySerializer(
            data={
                'name': 'a name',
                'schema': EXAMPLE_SCHEMA,
            },
            context={'request': self.request}
        )
        self.assertTrue(survey.is_valid())
        survey.save()

        response = ResponseSerializer(
            data={
                'survey': survey.data['id'],
                'data': {
                    'firstName': 'Peter',
                    # 'lastName': 'Pan',
                    'age': 99,
                },
            },
            context={'request': self.request}
        )
        self.assertFalse(response.is_valid(), 'missing required property')

        response = ResponseSerializer(
            data={
                'survey': survey.data['id'] + 99,
                'data': {
                    'firstName': 'Peter',
                    # 'lastName': 'Pan',
                    'age': 99,
                },
            },
            context={'request': self.request}
        )
        self.assertFalse(response.is_valid(),
                         'missing required property without REAL survey')

        response = ResponseSerializer(
            data={
                'survey': survey.data['id'],
                'data': {
                    'firstName': 'Peter',
                    'lastName': 'Pan',
                    'age': 99,
                },
            },
            context={'request': self.request}
        )
        self.assertTrue(response.is_valid())
