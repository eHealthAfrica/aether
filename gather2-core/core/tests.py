import json

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import Client, RequestFactory

from hypothesis import given, strategies
from hypothesis.extra.django import TestCase
from hypothesis.extra.django.models import models
from rest_framework import status

from .models import Survey

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

EXAMPLE_BAD_SCHEMA1 = "{'why is a string in a dict?'}"
EXAMPLE_BAD_SCHEMA2 = "\"[]\""
EXAMPLE_BAD_SCHEMA3 = "\"af[]23\""


UserGenerator = models(User, username=strategies.text(max_size=30), first_name=strategies.text(
    max_size=30), last_name=strategies.text(max_size=30), email=strategies.just('example@example.com'))

SurveyGenerator = models(Survey, schema=strategies.just(
    EXAMPLE_SCHEMA), created_by=UserGenerator)


SurveyGoalData = strategies.fixed_dictionaries(mapping={
    'schema': strategies.one_of(
        strategies.just(EXAMPLE_SCHEMA),
        strategies.text(),
        strategies.just(EXAMPLE_BAD_SCHEMA1),
        strategies.just(EXAMPLE_BAD_SCHEMA2),
        strategies.just(EXAMPLE_BAD_SCHEMA3),
    ),
    'created_by': strategies.integers(),
    'name': strategies.text(),
})


SurveyResponseGoal = strategies.fixed_dictionaries({
    'data': strategies.fixed_dictionaries({
        'firstName': strategies.text(),
        'lastName': strategies.text(),
        'created_by': strategies.integers(),
    }),
    'created_by': strategies.integers(),
    'survey': strategies.integers(),
})

GoodMapFunctionGoal = strategies.fixed_dictionaries({
    'code': strategies.just('print data'),
    'survey': strategies.integers(),
})

BadMapFunctionGoal = strategies.fixed_dictionaries({
    'code': strategies.just('1/0'),
    'survey': strategies.integers(),
})

UglyMapFunctionGoal = strategies.fixed_dictionaries({
    'code': strategies.text(),
    'survey': strategies.integers(),
})


class SimpleTestCase(TestCase):

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
        self.assertTrue(login)

        response = client.post(reverse('survey-list'),
                               json.dumps(data),
                               content_type='application/json')

        self.assertFalse(
            status.is_server_error(response.status_code), response.json())
        self.crawl('http://testserver' + reverse('api-root'), seen=[], client=client)

        for s in Survey.objects.all():
            assert isinstance(str(s), str)
            assert s.get_absolute_url()

    @given(SurveyResponseGoal)
    def test_survey_response_smoke_test(self, survey_response):
        client = Client()

        username = 'test'
        email = 'test@example.com'
        password = 'test'

        u = User.objects.create_user(username, email, password)

        login = client.login(username=username, password=password)
        self.assertTrue(login)

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
        self.crawl('http://testserver' + reverse('api-root'), seen=[], client=client)

    def test_reduce_function(self):
        client = Client()

        username = 'test'
        email = 'test@example.com'
        password = 'test'

        u = User.objects.create_user(username, email, password)

        login = client.login(username=username, password=password)
        self.assertTrue(login)

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

        response = client.post(reverse('response-list'),
                               json.dumps({
                                   "data": {"firstName": "tim", "lastName": "qux"},
                                   "survey": survey_id
                               }),
                               content_type='application/json')
        self.assertTrue(
            status.is_success(response.status_code), response.content)

        # Make a map function
        response = client.post(reverse('map_function-list'),
                               json.dumps({
                                   "code": "print data['firstName']",
                                   "survey": survey_id
                               }),
                               content_type='application/json')
        self.assertTrue(
            status.is_success(response.status_code), response.content)
        map_function_id = response.json()['id']

        # Make a reduce function
        response = client.post(reverse('reduce_function-list'),
                               json.dumps({
                                   "code": "print ''.join(data)",
                                   "map_function": map_function_id
                               }),
                               content_type='application/json')
        self.assertTrue(
            status.is_success(response.status_code), response.content)

        reduce_function_id = response.json()['id']

        # Assert the reduce function only gets the first name
        response = client.get(
            reverse('reduce_function-detail', args=[reduce_function_id]))
        self.assertEqual(response.json()['output'], ['tim'], response.content)

        # Add new Response
        response = client.post(reverse('response-list'),
                               json.dumps({
                                   "data": {"firstName": "bob", "lastName": "smith"},
                                   "survey": survey_id
                               }),
                               content_type='application/json')
        self.assertTrue(
            status.is_success(response.status_code), response.content)

        # Assert reduce function is recalcualted with new response included
        response = client.get(
            reverse('reduce_function-detail', args=[reduce_function_id]))
        self.assertEqual(response.json()['output'], ['timbob'])

        # Update Reduce function
        response = client.put(reverse('reduce_function-detail', args=[reduce_function_id]),
                              json.dumps({
                                  "code": "print '-'.join(d for d in data if d)",
                                  "map_function": map_function_id
                              }),
                              content_type='application/json')
        self.assertTrue(
            status.is_success(response.status_code), response.content)

        # Assert the reduce function is recalculated when updated
        response = client.get(
            reverse('reduce_function-detail', args=[reduce_function_id]))
        self.assertEqual(response.json()['output'], ['tim-bob'])

        # Updated the map function
        response = client.put(reverse('map_function-detail', args=[map_function_id]),
                              json.dumps({
                                  "code": "print data['lastName']",
                                  "survey": survey_id,
                              }),
                              content_type='application/json')
        self.assertTrue(
            status.is_success(response.status_code), response.content)

        # Assert reduce function is recalcualted with new map function
        response = client.get(
            reverse('reduce_function-detail', args=[reduce_function_id]))
        self.assertEqual(response.json()['output'], ['qux-smith'])

        self.crawl('http://testserver' + reverse('api-root'), seen=[], client=client)

    @given(UglyMapFunctionGoal)
    def test_map_function_smoke_test(self, map_function_data):
        client = Client()

        username = 'test'
        email = 'test@example.com'
        password = 'test'

        u = User.objects.create_user(username, email, password)

        login = client.login(username=username, password=password)
        self.assertTrue(login)

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

        response = client.post(reverse('map_function-list'),
                               json.dumps(map_function_data),
                               content_type='application/json')

        self.assertFalse(
            status.is_server_error(response.status_code), response.content)
        self.crawl('http://testserver' + reverse('api-root'), seen=[], client=client)

    @given(SurveyResponseGoal)
    def test_response_smoke_test(self, survey_response):
        client = Client()

        username = 'test'
        email = 'test@example.com'
        password = 'test'

        u = User.objects.create_user(username, email, password)

        login = client.login(username=username, password=password)
        self.assertTrue(login)

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
        response = client.post(reverse('map_function-list'),
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
        response = client.post(reverse('map_function-list'),
                               json.dumps(map_code),
                               content_type='application/json')

        self.assertTrue(
            status.is_success(response.status_code), response.content)

        # A good function
        map_code = {
            'code': '''print data''',
            'survey': survey_id
        }
        response = client.post(reverse('map_function-list'),
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

        self.crawl('http://testserver' + reverse('api-root'), seen=[], client=client)

    def crawl(self, obj, seen=[], client=None):
        '''
        Crawls the API for urls to assert that all GET  requests do not error.
        '''

        if not client:
            client = Client()

        if isinstance(obj, dict):
            {k: self.crawl(v, seen, client) for k, v in obj.items()}
        elif isinstance(obj, list):
            [self.crawl(elem, seen, client) for elem in obj]
        elif isinstance(obj, str):
            # Is this a url?
            if obj.startswith('http://') and (obj not in seen):
                seen.append(obj)
                response = client.get(obj)
                self.assertFalse(
                    status.is_server_error(response.status_code), response.content)
                self.crawl(response.json(), seen)

    def test_json_serializer(self):
        # Just random tests to get coverage up.

        # This is to test that the json will be parsed correctly in the api
        # form
        from core.serializers import JSONSerializer
        self.assertEqual(str(JSONSerializer().to_representation(1)), '1')

        # This also tests that the json will be parsed correctly in the api
        # form
        from core.serializers import SurveySerializer

        r = RequestFactory().get('/')
        username = 'test'
        email = 'test@example.com'
        password = 'test'
        u = User.objects.create_user(username, email, password)
        r.user = u
        s = SurveySerializer(
            data={'survey': '2', 'schema': '{}'}, context={'request': r})
        s.is_valid()

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
        self.assertTrue(login)

        response = client.post(reverse('survey-list'), {
            'name': 'b_survey',
            'schema': json.dumps(EXAMPLE_SCHEMA),
        })
        self.assertEqual(
            response.status_code, 201, response.content.decode('utf-8'))

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
        self.assertEqual(
            response.status_code, 400, response.content.decode('utf-8'))

    def test_query_nested_data_by_string(self):

        client = Client()

        username = 'test'
        email = 'test@example.com'
        password = 'test'

        User.objects.create_superuser(username, email, password)

        login = client.login(username=username, password=password)
        self.assertTrue(login)

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

        self.assertEqual(response.status_code, 200, response_json)
        self.assertEqual(
            response_json['results'][0]['data']['firstName'], "Peter")
