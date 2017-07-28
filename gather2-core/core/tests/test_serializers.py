from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from ..serializers import SurveySerializer


class SerializersTests(TestCase):

    def setUp(self):
        username = 'test'
        email = 'test@example.com'
        password = 'testtest'

        self.request = RequestFactory().get('/')
        self.request.user = get_user_model().objects.create_superuser(username, email, password)

    def test_survey_serializer_1(self):
        survey = SurveySerializer(
            data={
                # missing 'name': 'a name',
                'survey': '2',
                'schema': {},
            },
            context={'request': self.request}
        )
        self.assertFalse(survey.is_valid())

    def test_survey_serializer_2(self):
        survey = SurveySerializer(
            data={
                'name': 'a name',
                'survey': '2',
                'schema': '{ "something wrong" }',  # wrong schema
            },
            context={'request': self.request}
        )
        self.assertFalse(survey.is_valid())

    def test_survey_serializer_3(self):
        survey = SurveySerializer(
            data={
                'name': 'a name',
                'survey': '2',
                'schema': '{}',
            },
            context={'request': self.request}
        )
        self.assertTrue(survey.is_valid())

    def test_survey_serializer_4(self):
        survey = SurveySerializer(
            data={
                'name': 'a name',
                'survey': '2',
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
