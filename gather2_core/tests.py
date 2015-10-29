import pytest
import json

from django.test import Client
from django.contrib.auth.models import User

from .models import Survey

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


@pytest.mark.django_db
def test_my_user():
    a = Survey(name="Hello World")
    assert str(a) == "None - Hello World"


@pytest.mark.django_db
def test_create_survey():

    client = Client()

    username = 'test'
    email = 'test@example.com'
    password = 'test'

    User.objects.create_superuser(username, email, password)

    login = client.login(username=username, password=password)
    assert login is True

    response = client.post('/surveys/', data={
        'name': 'a_survey',
        'schema': '22',
    })
    assert response.status_code == 201, response.content.decode('utf-8')


@pytest.mark.django_db
def test_create_3_items_for_survey():

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
    assert response.status_code == 201, response.content.decode('utf-8')

    response_json = json.loads(response.content.decode('utf-8'))

    survey_id = response_json['id']
    items_url = response_json['surveyitems']

    data = {
        'survey': survey_id,
        # ^- TODO this must go because we're POSTing to the survey's items url already

        'data': json.dumps({
            'firstName': 'Peter',
            'lastName': 'Pan',
            'age': 99,
        }),
    }

    response = client.post(items_url, data=data)
    response_json = json.loads(response.content.decode('utf-8'))
    assert response.status_code == 201, response_json

    # TODO
    # assert response_json['url'].startswith(items_url)

    response = client.post(items_url, data=data)
    response_json = json.loads(response.content.decode('utf-8'))
    assert response.status_code == 201, response_json

    response = client.post(items_url, data=data)
    response_json = json.loads(response.content.decode('utf-8'))
    assert response.status_code == 201, response_json


@pytest.mark.django_db
def test_create_item_for_survey_that_does_not_fit_schema():

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
    assert response.status_code == 201, response.content.decode('utf-8')

    response_json = json.loads(response.content.decode('utf-8'))

    survey_id = response_json['id']
    items_url = response_json['surveyitems']

    data = {
        'survey': survey_id,
        # ^- TODO this must go because we're POSTing to the survey's items url already

        'data': json.dumps({
            'firstName': 'Peter',
            # missing: "lastName"
            'age': 99,
        }),
    }

    response = client.post(items_url, data=data)
    response_json = json.loads(response.content.decode('utf-8'))
    assert response.status_code == 400, response.content.decode('utf-8')


@pytest.mark.django_db
def test_query_nested_data_by_string():

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
    items_url = response_json['surveyitems']

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

    response = client.get("/items/?data__firstName=Peter")
    response_json = json.loads(response.content.decode('utf-8'))

    assert response.status_code == 200, response_json
    assert response_json['count'] == 1
    assert response_json['results'][0]['data']['firstName'] == "Peter"
