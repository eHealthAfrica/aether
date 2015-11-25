import json
from django.test import Client, RequestFactory
from .models import Survey, Response
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from hypothesis.extra.django import TestCase
from hypothesis import given
from hypothesis.extra.django.models import models
from hypothesis import strategies
from rest_framework import status


User = get_user_model()

EXAMPLE_SCHEMA = {
    "title": "Example Schema",
    "type": "object",
    "properties": {
        "firstName": {
            "type": "string"
        },
        "lastName": {
            "type": "string"
        },
        "age": {
            "description": "Age",
            "type": "integer",
            "minimum": 0
        }
    },
    "required": ["firstName", "lastName"]
}

EXAMPLE_BAD_SCHEMA = "{'why is a string in a dict?'}"


user_1 = models(User, username=strategies.text(max_size=30), first_name=strategies.text(
    max_size=30), last_name=strategies.text(max_size=30)).example()

SurveyGoalData = strategies.fixed_dictionaries(mapping={
    "schema": strategies.one_of(
        strategies.just(EXAMPLE_SCHEMA),
        strategies.text(),
        strategies.just(EXAMPLE_BAD_SCHEMA),
    ),
    "created_by": strategies.integers(),
    "name": strategies.text(),
})


SurveyResponseGoal = strategies.fixed_dictionaries({
    'data': strategies.fixed_dictionaries({
        'firstName': strategies.text(),
        'lastName': strategies.text(),
        'created_by': strategies.integers(),
    }),
    "created_by": strategies.integers(),
    "survey": strategies.integers(),
})

UglyMapFunctionResponseGoal = strategies.fixed_dictionaries({
    'code': strategies.text(),
    "survey": strategies.integers(),
})


class SimpleTestCase(TestCase):

    def test_my_user(self):
        a = Survey(name="Hello World", schema=EXAMPLE_SCHEMA)
        assert str(a) == "None - Hello World"

    @given(SurveyGoalData)
    def test_survey_smoke_test(self, data):

        client = Client()

        # First test with an unauthenticated user

        username = 'test'
        email = 'test@example.com'
        password = 'test'

        User.objects.create_user(username, email, password)

        response = client.post(reverse('survey-list'),
                               json.dumps(data),
                               content_type='application/json')

        self.assertFalse(
            status.is_server_error(response.status_code), response.json())

        # Now test with a logged in user
        login = client.login(username=username, password=password)
        assert login is True

        response = client.post(reverse('survey-list'),
                               json.dumps(data),
                               content_type='application/json')

        self.assertFalse(
            status.is_server_error(response.status_code), response.json())
        self.crawl('http://testserver' + reverse('api-root'), seen=[])

    @given(SurveyResponseGoal)
    def test_survey_response_smoke_test(self, survey_response):
        client = Client()

        username = 'test'
        email = 'test@example.com'
        password = 'test'

        u = User.objects.create_user(username, email, password)

        login = client.login(username=username, password=password)
        assert login is True

        response = client.post(reverse('response-list'),
                               json.dumps(survey_response),
                               content_type='application/json')

        self.assertFalse(
            status.is_server_error(response.status_code), response.json())

        # Make a survey
        s = {
            'owner': u.id,
            'name': 'a title',
            'schema': EXAMPLE_SCHEMA
        }
        response = client.post(reverse('survey-list'),
                               json.dumps(s),
                               content_type='application/json')

        self.assertTrue(
            status.is_success(response.status_code), response.content)

        # Upload the result again

        survey_response['survey'] = response.json()['id']

        response = client.post(reverse('response-list'),
                               json.dumps(survey_response),
                               content_type='application/json')

        self.assertTrue(
            status.is_success(response.status_code), response.content)
        self.crawl('http://testserver' + reverse('api-root'), seen=[])

    @given(UglyMapFunctionResponseGoal)
    def test_map_function_smoke_test(self, map_function_data):
        client = Client()

        username = 'test'
        email = 'test@example.com'
        password = 'test'

        u = User.objects.create_user(username, email, password)

        login = client.login(username=username, password=password)
        assert login is True

        # Make a survey
        s = {
            'owner': u.id,
            'name': 'a title',
            'schema': EXAMPLE_SCHEMA
        }
        response = client.post(reverse('survey-list'),
                               json.dumps(s),
                               content_type='application/json')

        self.assertTrue(
            status.is_success(response.status_code), response.content)

        response = client.post(reverse('map_functions-list'),
                               json.dumps(map_function_data),
                               content_type='application/json')

        self.assertFalse(
            status.is_server_error(response.status_code), response.content)
        self.crawl('http://testserver' + reverse('api-root'), seen=[])

    @given(SurveyResponseGoal)
    def test_response_smoke_test(self, survey_response):
        client = Client()

        username = 'test'
        email = 'test@example.com'
        password = 'test'

        u = User.objects.create_user(username, email, password)

        login = client.login(username=username, password=password)
        assert login is True

        # Make a survey
        s = {
            'owner': u.id,
            'name': 'a title',
            'schema': EXAMPLE_SCHEMA
        }
        response = client.post(reverse('survey-list'),
                               json.dumps(s),
                               content_type='application/json')

        self.assertTrue(
            status.is_success(response.status_code), response.content)
        survey_id = response.json()['id']

        # A bad function!
        map_code = {
            'code': '''1/0''',
            'survey': survey_id
        }
        response = client.post(reverse('map_functions-list'),
                               json.dumps(map_code),
                               content_type='application/json')

        self.assertTrue(
            status.is_success(response.status_code), response.content)

        # A bad response because <type 'object'> cannot be converted to a
        # literal.
        map_code = {
            'code': '''print object()''',
            'survey': survey_id
        }
        response = client.post(reverse('map_functions-list'),
                               json.dumps(map_code),
                               content_type='application/json')

        self.assertTrue(
            status.is_success(response.status_code), response.content)

        # A good function
        map_code = {
            'code': '''print data''',
            'survey': survey_id
        }
        response = client.post(reverse('map_functions-list'),
                               json.dumps(map_code),
                               content_type='application/json')

        self.assertTrue(
            status.is_success(response.status_code), response.content)

        # Make sure we use a real survey
        survey_response['survey'] = survey_id

        response = client.post(reverse('response-list'),
                               json.dumps(survey_response),
                               content_type='application/json')

        self.assertTrue(
            status.is_success(response.status_code), response.content)

        self.crawl('http://testserver' + reverse('api-root'), seen=[])

    def crawl(self, obj, seen=[]):
        if isinstance(obj, dict):
            {k: self.crawl(v, seen) for k, v in obj.items()}
        elif isinstance(obj, list):
            [self.crawl(elem, seen) for elem in obj]
        elif isinstance(obj, str):
            # Is this a url?
            if obj.startswith('http://') and (obj not in seen):
                seen.append(obj)
                client = Client()
                response = client.get(obj)
                self.assertTrue(
                    status.is_success(response.status_code), response.content)
                self.crawl(response.json(), seen)

    def test_json_serializer(self):
        # Just random tests to get coverage up.

        # This is to test that the json will be parsed correctly in the api
        # form
        from core.serializers import JSONSerializer
        self.assertEqual(str(JSONSerializer().to_representation(1)), '1')

        # This also tests that the json will be parsed correctly in the api
        # form
        from core.serializers import SurveySerialzer

        r = RequestFactory().get('/')
        username = 'test'
        email = 'test@example.com'
        password = 'test'
        u = User.objects.create_user(username, email, password)
        r.user = u
        s = SurveySerialzer(
            data={'survey': '2', 'schema': '"123,3"'}, context={'request': r})
        s.is_valid()

    def test_query_decorator(self):
        qs = Response.objects.all().decorate('123').decorate('123')
        self.assertEqual(['123'], qs._decorate_funcs)

    def test_template_names(self):
        url = reverse('survey-list', kwargs={'format': 'html'})
        client = Client()
        response = client.get(url)
        self.assertTrue(
            status.is_success(response.status_code), response.content)

    def test_app_config(self):
        from django.apps import apps
        self.assertEquals(apps.get_app_config('core').verbose_name, 'Core')

    def test_create_item_for_survey_that_does_not_fit_schema(self):

        client = Client()

        username = 'test'
        email = 'test@example.com'
        password = 'test'

        User.objects.create_superuser(username, email, password)

        login = client.login(username=username, password=password)
        assert login is True

        response = client.post(reverse('survey-list'), {
            'name': 'b_survey',
            'schema': json.dumps(EXAMPLE_SCHEMA),
        })
        assert response.status_code == 201, response.content.decode('utf-8')

        response_json = json.loads(response.content.decode('utf-8'))

        survey_id = response_json['id']
        items_url = response_json['responses_url']

        data = {
            'survey': survey_id,
            'data': json.dumps({
                'firstName': 'Peter',
                # missing: "lastName"
                'age': 99,
            }),
        }

        response = client.post(items_url, data=data)
        response_json = json.loads(response.content.decode('utf-8'))
        assert response.status_code == 400, response.content.decode('utf-8')

    def test_query_nested_data_by_string(self):

        client = Client()

        username = 'test'
        email = 'test@example.com'
        password = 'test'

        User.objects.create_superuser(username, email, password)

        login = client.login(username=username, password=password)
        assert login is True

        response = client.post('/surveys/', data={
            'name': 'b_survey',
            'schema': json.dumps(EXAMPLE_SCHEMA),
        })

        response_json = json.loads(response.content.decode('utf-8'))

        survey_id = response_json['id']
        items_url = response_json['responses_url']

        def gen_data(offset):
            return {
                'survey': survey_id,
                # ^- TODO this must go because we're POSTing to the survey's items url already

                'data': json.dumps({
                    'firstName': ['Joe', 'Peter', 'Tom'][offset],
                    'lastName': 'Pan',
                    'age': 98 + offset,
                }),
            }

        client.post(items_url, data=gen_data(0))
        client.post(items_url, data=gen_data(1))
        client.post(items_url, data=gen_data(2))

        response = client.get("/responses/?data__firstName=Peter")
        response_json = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 200, response_json
        assert response_json['results'][0]['data']['firstName'] == "Peter"
