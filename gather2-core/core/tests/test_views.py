import json

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TransactionTestCase

from hypothesis import given, strategies
from rest_framework import status


EXAMPLE_SCHEMA = {
    'title': 'Example Schema',
    'type': 'object',
    'properties': {
        'firstName': {
            'type': 'string'
        },
        'lastName': {
            'type': 'string'
        },
        'age': {
            'description': 'Age',
            'type': 'integer',
            'minimum': 0
        }
    },
    'required': ['firstName', 'lastName']
}

EXAMPLE_BAD_SCHEMA1 = '{"why is a string in a dict?"}'
EXAMPLE_BAD_SCHEMA2 = '"[]"'
EXAMPLE_BAD_SCHEMA3 = '"af[]23"'
EXAMPLE_BAD_SCHEMA4 = '"{}"'


SurveyGoalData = strategies.fixed_dictionaries(mapping={
    'schema': strategies.one_of(
        strategies.just(EXAMPLE_SCHEMA),
        strategies.text(),
        strategies.just(EXAMPLE_BAD_SCHEMA1),
        strategies.just(EXAMPLE_BAD_SCHEMA2),
        strategies.just(EXAMPLE_BAD_SCHEMA3),
        strategies.just(EXAMPLE_BAD_SCHEMA4),
    ),
    'created_by': strategies.integers(),
    'name': strategies.text(),
})

SurveyResponseGoal = strategies.fixed_dictionaries(mapping={
    'data': strategies.fixed_dictionaries({
        'firstName': strategies.text(),
        'lastName': strategies.text(),
        'created_by': strategies.integers(),
    }),
    'created_by': strategies.integers(),
    'survey': strategies.integers(),
})

GoodMapFunctionGoal = strategies.fixed_dictionaries(mapping={
    'code': strategies.just('print data'),
    'survey': strategies.integers(),
})

BadMapFunctionGoal = strategies.fixed_dictionaries(mapping={
    'code': strategies.just('1/0'),
    'survey': strategies.integers(),
})

UglyMapFunctionGoal = strategies.fixed_dictionaries(mapping={
    'code': strategies.text(),
    'survey': strategies.integers(),
})


class ViewsTest(TransactionTestCase):

    def setUp(self):
        username = 'test'
        email = 'test@example.com'
        password = 'testtest'

        self.user = get_user_model().objects.create_superuser(username, email, password)

        # Make a survey
        self.survey = {
            'owner': self.user.id,
            'name': 'a title',
            'schema': EXAMPLE_SCHEMA
        }

        # Now test with a logged in user
        self.assertTrue(self.client.login(username=username, password=password))

    def tearDown(self):
        self.client.logout()

    def crawl(self, obj, seen=[]):
        '''
        Crawls the API for urls to assert that all GET requests do not error.
        '''

        if isinstance(obj, dict):
            {k: self.crawl(v, seen) for k, v in obj.items()}
        elif isinstance(obj, list):
            [self.crawl(elem, seen) for elem in obj]
        elif isinstance(obj, str):
            # Is this a url?
            if obj.startswith('http://') and (obj not in seen):
                seen.append(obj)
                response = self.client.get(obj)
                self.assertFalse(status.is_server_error(response.status_code), response.json())
                self.crawl(response.json(), seen)

    @given(SurveyGoalData)
    def test_survey_smoke_test(self, data):
        response = self.client.post(reverse('survey-list'),
                                    data=json.dumps(data),
                                    content_type='application/json')
        self.assertFalse(status.is_server_error(response.status_code), response.json())

        self.client.logout()
        response = self.client.post(reverse('survey-list'),
                                    data=json.dumps(data),
                                    content_type='application/json')
        self.assertFalse(status.is_server_error(response.status_code), response.json())

    @given(SurveyResponseGoal)
    def test_survey_response_smoke_test(self, survey_response):
        response = self.client.post(reverse('response-list'),
                                    data=json.dumps(survey_response),
                                    content_type='application/json')
        self.assertFalse(status.is_server_error(response.status_code), response.json())

        response = self.client.post(reverse('survey-list'),
                                    data=json.dumps(self.survey),
                                    content_type='application/json')
        self.assertTrue(status.is_success(response.status_code), response.json())

        # Upload the result again
        survey_response['survey'] = response.json()['id']
        response = self.client.post(reverse('response-list'),
                                    data=json.dumps(survey_response),
                                    content_type='application/json')
        self.assertTrue(status.is_success(response.status_code), response.json())

    def test_reduce_function(self):
        # Make survey
        response = self.client.post(reverse('survey-list'),
                                    data=json.dumps(self.survey),
                                    content_type='application/json')
        self.assertTrue(status.is_success(response.status_code), response.json())
        survey_id = response.json()['id']

        # Make a map function
        response = self.client.post(reverse('map_function-list'),
                                    data=json.dumps({
                                        'code': '''print data['firstName']''',
                                        'survey': survey_id
                                    }),
                                    content_type='application/json')
        self.assertTrue(status.is_success(response.status_code), response.json())
        map_function_id = response.json()['id']

        # Make a reduce function
        response = self.client.post(reverse('reduce_function-list'),
                                    data=json.dumps({
                                        'code': '''print ''.join(data)''',
                                        'map_function': map_function_id
                                    }),
                                    content_type='application/json')
        self.assertTrue(status.is_success(response.status_code), response.json())
        reduce_function_id = response.json()['id']

        # Add response
        response = self.client.post(reverse('response-list'),
                                    data=json.dumps({
                                        'data': {'firstName': 'tim', 'lastName': 'qux'},
                                        'survey': survey_id
                                    }),
                                    content_type='application/json')
        self.assertTrue(status.is_success(response.status_code), response.json())

        # Assert the reduce function only gets the first name
        response = self.client.get(reverse('reduce_function-detail', args=[reduce_function_id]))
        self.assertEqual(response.json()['output'], ['tim'], response.json())

        # Add new Response
        response = self.client.post(reverse('response-list'),
                                    data=json.dumps({
                                        'data': {'firstName': 'bob', 'lastName': 'smith'},
                                        'survey': survey_id
                                    }),
                                    content_type='application/json')
        self.assertTrue(status.is_success(response.status_code), response.json())

        # Assert reduce function is recalculated with new response included
        response = self.client.get(reverse('reduce_function-detail', args=[reduce_function_id]))
        self.assertEqual(response.json()['output'], ['timbob'])

        # Update Reduce function
        response = self.client.put(reverse('reduce_function-detail', args=[reduce_function_id]),
                                   data=json.dumps({
                                       'code': '''print '-'.join(d for d in data if d)''',
                                       'map_function': map_function_id
                                   }),
                                   content_type='application/json')
        self.assertTrue(status.is_success(response.status_code), response.json())

        # Assert the reduce function is recalculated when updated
        response = self.client.get(reverse('reduce_function-detail', args=[reduce_function_id]))
        self.assertEqual(response.json()['output'], ['tim-bob'])

        # Updated the map function
        response = self.client.put(reverse('map_function-detail', args=[map_function_id]),
                                   data=json.dumps({
                                       'code': '''print data['lastName']''',
                                       'survey': survey_id,
                                   }),
                                   content_type='application/json')
        self.assertTrue(status.is_success(response.status_code), response.json())

        # Assert reduce function is recalculated with new map function
        response = self.client.get(reverse('reduce_function-detail', args=[reduce_function_id]))
        self.assertEqual(response.json()['output'], ['qux-smith'])

        # with all the data tree created, test that all the given urls work
        self.crawl('http://testserver' + reverse('api-root'), seen=[])

    @given(UglyMapFunctionGoal)
    def test_map_function_smoke_test(self, map_function_data):
        response = self.client.post(reverse('survey-list'),
                                    data=json.dumps(self.survey),
                                    content_type='application/json')
        self.assertTrue(status.is_success(response.status_code), response.json())

        response = self.client.post(reverse('map_function-list'),
                                    data=json.dumps(map_function_data),
                                    content_type='application/json')
        self.assertFalse(status.is_server_error(response.status_code), response.json())

    @given(SurveyResponseGoal)
    def test_response_smoke_test(self, survey_response):
        response = self.client.post(reverse('survey-list'),
                                    data=json.dumps(self.survey),
                                    content_type='application/json')
        self.assertTrue(status.is_success(response.status_code), response.json())
        survey_id = response.json()['id']

        # A bad function!
        map_code = {
            'code': '''1/0''',
            'survey': survey_id
        }
        response = self.client.post(reverse('map_function-list'),
                                    data=json.dumps(map_code),
                                    content_type='application/json')
        self.assertTrue(status.is_success(response.status_code), response.json())

        # A bad response because <type 'object'> cannot be converted to a literal.
        map_code = {
            'code': '''print object()''',
            'survey': survey_id
        }
        response = self.client.post(reverse('map_function-list'),
                                    data=json.dumps(map_code),
                                    content_type='application/json')
        self.assertTrue(status.is_success(response.status_code), response.json())

        # A good function
        map_code = {
            'code': '''print data''',
            'survey': survey_id
        }
        response = self.client.post(reverse('map_function-list'),
                                    data=json.dumps(map_code),
                                    content_type='application/json')
        self.assertTrue(status.is_success(response.status_code), response.json())

        # Make sure we use a real survey
        survey_response['survey'] = survey_id
        response = self.client.post(reverse('response-list'),
                                    data=json.dumps(survey_response),
                                    content_type='application/json')
        self.assertTrue(status.is_success(response.status_code), response.json())

    def test_create_item_for_survey_that_does_not_fit_schema(self):
        response = self.client.post(reverse('survey-list'),
                                    data=json.dumps({
                                        'name': 'b_survey',
                                        'schema': EXAMPLE_SCHEMA
                                    }),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201, response.json())

        response_json = response.json()
        survey_id = response_json['id']
        items_url = response_json['responses_url']

        data = {
            'survey': survey_id,
            'data': {
                'firstName': 'Peter',
                # missing: 'lastName': 'Pan',
                'age': 99,
            },
        }

        response = self.client.post(items_url,
                                    data=json.dumps(data),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400, response.json())

    def test_query_nested_data_by_string(self):
        response = self.client.post(reverse('survey-list'),
                                    data=json.dumps({
                                        'name': 'b_survey',
                                        'schema': EXAMPLE_SCHEMA
                                    }),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201, response.json())

        response_json = response.json()
        survey_id = response_json['id']
        items_url = response_json['responses_url']

        def gen_data(offset):
            return {
                'survey': survey_id,
                'data': {
                    'firstName': ['Joe', 'Peter', 'Tom'][offset],
                    'lastName': 'Pan',
                    'age': 98 + offset,
                },
            }

        for i in range(3):
            response = self.client.post(items_url,
                                        data=json.dumps(gen_data(i)),
                                        content_type='application/json')
            self.assertTrue(status.is_success(response.status_code), response.json())

        response = self.client.get('/responses/?data__firstName=Peter')
        self.assertEqual(response.status_code, 200, response.json())

        data = response.json()['results']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['data']['firstName'], 'Peter')

        # check survey stats
        response = self.client.get('/surveys-stats/')
        self.assertEqual(response.status_code, 200, response.json())

        data = response.json()['results']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['responses'], 3, '3 responses were created')
