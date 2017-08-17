import json

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TransactionTestCase

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

EXAMPLE_CODE_UNSAFE_1 = '''
import os
# it has no access to app variables but... it scares!!!
print os.environ.get('RDS_HOSTNAME')
'''

EXAMPLE_CODE_UNSAFE_2 = '''
import sys
print(sys.exc_info())
sys.exit(-1)
'''


class ViewsTest(TransactionTestCase):

    def setUp(self):
        username = 'test'
        email = 'test@example.com'
        password = 'testtest'
        self.user = get_user_model().objects.create_user(username, email, password)
        self.assertTrue(self.client.login(username=username, password=password))

        self.survey = {
            'owner': self.user.id,
            'name': 'a title',
            'schema': EXAMPLE_SCHEMA,
        }

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
                self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
                self.crawl(response.json(), seen)

    def helper_post(self, url, data, expected_status=status.HTTP_201_CREATED):
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, expected_status, response.json())
        if expected_status == status.HTTP_201_CREATED:
            return response.json()

    def helper_put(self, url, data, expected_status=status.HTTP_200_OK):
        response = self.client.put(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, expected_status, response.json())

    def helper_get_list(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        return response.json()['results']

    def helper_create_survey(self):
        survey = self.helper_post(url=reverse('survey-list'), data=self.survey)
        return survey['id'], survey['responses_url']

    def helper_test_map_function(self, code):
        survey_id, items_url = self.helper_create_survey()
        self.helper_post(
            url=items_url,
            data={
                'survey': survey_id,
                'data': {
                    'firstName': 'Peter',
                    'lastName': 'Pan',
                    'age': 99,
                },
            },
        )
        map_function = self.helper_post(
            url=reverse('map_function-list'),
            data={
                'code': code,
                'survey': survey_id,
            },
        )
        results_url = map_function['results_url']
        results = self.helper_get_list(results_url)
        self.assertEqual(len(results), 1)
        return results[0]['output'], results[0]['error']

    def test_survey(self):
        # Make surveys with bad schemas
        self.helper_post(
            url=reverse('survey-list'),
            data={
                'owner': self.user.id,
                'name': 'a title',
                'schema': '{"why is a string in a dict?"}',
            },
            expected_status=status.HTTP_400_BAD_REQUEST,
        )
        self.helper_post(
            url=reverse('survey-list'),
            data={
                'owner': self.user.id,
                'name': 'a title',
                'schema': '"[]"',
            },
            expected_status=status.HTTP_400_BAD_REQUEST,
        )
        self.helper_post(
            url=reverse('survey-list'),
            data={
                'owner': self.user.id,
                'name': 'a title',
                'schema': '"{}"',
            },
            expected_status=status.HTTP_400_BAD_REQUEST,
        )

        # try to create a survey without credentials
        self.client.logout()
        self.helper_post(
            url=reverse('survey-list'),
            data=self.survey,
            expected_status=status.HTTP_403_FORBIDDEN,
        )

    def test_response__not_fit_survey_schema(self):
        survey_id, items_url = self.helper_create_survey()
        self.helper_post(
            url=items_url,
            data={
                'survey': survey_id,
                'data': {
                    'firstName': 'Peter',
                    # missing: 'lastName': 'Pan',
                    'age': 99,
                },
            },
            expected_status=status.HTTP_400_BAD_REQUEST,
        )

    def test_response__query_nested_data_by_string(self):
        survey_id, items_url = self.helper_create_survey()

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
            self.helper_post(url=items_url, data=gen_data(i))

        results = self.helper_get_list('/responses/?data__firstName=Peter')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['data']['firstName'], 'Peter')

        # check survey stats
        results = self.helper_get_list('/surveys-stats/')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['responses'], 3, '3 responses were created')

    def test_map_function__zero_division(self):
        output, error = self.helper_test_map_function(code='''1/0''')
        self.assertEqual(output, '')
        self.assertIn('ZeroDivisionError: integer division by zero', error)

    def test_map_function__print_object(self):
        output, error = self.helper_test_map_function(code='''print object()''')
        self.assertIn('<object object at', output)
        self.assertEqual(error, '')

    def test_map_function__unsafe_1(self):
        output, error = self.helper_test_map_function(code=EXAMPLE_CODE_UNSAFE_1)
        self.assertEqual(output, '')
        self.assertEqual(error, '')

    def test_map_function__unsafe_2(self):
        output, error = self.helper_test_map_function(code=EXAMPLE_CODE_UNSAFE_2)
        self.assertNotEqual(output, '')
        self.assertNotEqual(error, '')

    def test_full_workflow(self):
        # Make survey
        survey_id, _ = self.helper_create_survey()

        # Make a map function
        map_function = self.helper_post(
            url=reverse('map_function-list'),
            data={
                'code': '''print data['firstName']''',
                'survey': survey_id,
            },
        )
        map_function_id = map_function['id']

        # Make a reduce function
        reduce_function = self.helper_post(
            url=reverse('reduce_function-list'),
            data={
                'code': '''print ''.join(data)''',
                'map_function': map_function_id,
            },
        )
        reduce_function_id = reduce_function['id']

        # Add response
        self.helper_post(
            url=reverse('response-list'),
            data={
                'data': {'firstName': 'tim', 'lastName': 'qux'},
                'survey': survey_id,
            },
        )

        # Assert the reduce function only gets the first name
        response = self.client.get(reverse('reduce_function-detail', args=[reduce_function_id]))
        self.assertEqual(response.json()['output'], ['tim'], response.json())

        # Add new Response
        self.helper_post(
            url=reverse('response-list'),
            data={
                'data': {'firstName': 'bob', 'lastName': 'smith'},
                'survey': survey_id,
            },
        )

        # Assert reduce function is recalculated with new response included
        response = self.client.get(reverse('reduce_function-detail', args=[reduce_function_id]))
        self.assertEqual(response.json()['output'], ['timbob'])

        # Update Reduce function
        self.helper_put(
            url=reverse('reduce_function-detail', args=[reduce_function_id]),
            data={
                'code': '''print '-'.join(d for d in data if d)''',
                'map_function': map_function_id
            },
        )

        # Assert the reduce function is recalculated when updated
        response = self.client.get(reverse('reduce_function-detail', args=[reduce_function_id]))
        self.assertEqual(response.json()['output'], ['tim-bob'])

        # Update the map function
        self.helper_put(
            url=reverse('map_function-detail', args=[map_function_id]),
            data={
                'code': '''print data['lastName']''',
                'survey': survey_id,
            },
        )

        # Assert reduce function is recalculated with new map function
        response = self.client.get(reverse('reduce_function-detail', args=[reduce_function_id]))
        self.assertEqual(response.json()['output'], ['qux-smith'])

        # With all the data tree created, test that all the given urls work
        self.crawl('http://testserver' + reverse('api-root'), seen=[])
