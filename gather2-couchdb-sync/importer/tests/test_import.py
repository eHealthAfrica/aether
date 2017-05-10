from django.test import TestCase
import requests

from api.models import DeviceDB
from couchdb_tools import api
from api.tests import clean_couch
from ..import_couchdb import import_synced_devices, get_meta_doc, get_survey_mapping
from django.conf import settings
from api.couchdb_helpers import generate_password as random_string

device_id = 'test_import-from-couch'
auth_headers = {'Authorization': 'Token {}'.format(settings.GATHER_CORE_TOKEN), 'Content-Type': 'application/json'}


def get_gather_docs():
    url = '{}/responses/'.format(settings.GATHER_CORE_URL)
    resp = requests.get(url, headers=auth_headers)
    results = resp.json()['results']
    return results


example_survey = {
    "name": "example",
    "schema": {
        "title": "example",
        "properties": {
            "firstName": {
                "type": "string"
            },
            "lastName": {
                "type": "string"
            },
        },
        "required": ["firstName", "lastName"],
    }
}

example_doc = {
    '_id': "example-aabbbdddccc",
    'deviceId': device_id,
    'firstName': 'Han',
    'lastName': 'Solo'
}


class ImportTestCase(TestCase):
    def setUp(self):
        super().setUp()
        url = '{}/surveys/'.format(settings.GATHER_CORE_URL)
        example_survey['name'] = 'example'
        resp = requests.post(url, json=example_survey, headers=auth_headers).json()
        self.survey_id = resp['id']

    def tearDown(self):
        super().tearDown()
        if self.survey_id:
            url = '{}/surveys/{}'.format(settings.GATHER_CORE_URL, self.survey_id)
            requests.delete(url, headers=auth_headers)
        clean_couch()

    def test_import_one_document(self):
        clean_couch()
        # this creates a test couchdb
        device = DeviceDB(device_id=device_id)
        device.save()

        resp = api.put('{}/{}'.format(device.db_name, example_doc['_id']), json=example_doc)
        self.assertEqual(resp.status_code, 201, 'The example document got created')

        import_synced_devices()

        data = get_gather_docs()
        posted = data[0]  # Gather responds with the latest post first

        self.assertEqual(posted['survey'], self.survey_id, 'Survey posted ot the correct id, identified via survey name')
        for key in ['_id', 'firstName', 'lastName']:
            self.assertEqual(posted['data'].get(key), example_doc.get(key), 'posted example doc')

        # check the written meta document
        status = get_meta_doc(device.db_name, example_doc['_id'])

        self.assertFalse('error' in status, 'no error key')
        self.assertTrue('last_rev' in status, 'last rev key')
        self.assertTrue('gather_id' in status, 'gather id key')

    def test_dont_reimport_document(self):
        clean_couch()
        # this creates a test couchdb
        device = DeviceDB(device_id=device_id)
        device.save()

        resp = api.put('{}/{}'.format(device.db_name, example_doc['_id']), json=example_doc)
        self.assertEqual(resp.status_code, 201, 'The example document got created')

        import_synced_devices()

        # reset the user to test the meta doc mechanism
        device.last_synced_seq = 0
        device.save()

        import_synced_devices()

        data = get_gather_docs()
        last = data[0]['data']
        if data[1]:
            second_last = data[1]['data']
        else:
            second_last = {}

        for key in ['_id', 'firstName', 'lastName']:
            self.assertNotEqual(last.get(key), second_last.get(key))

    def test_update_document(self):
        clean_couch()
        # this creates a test couchdb
        device = DeviceDB(device_id=device_id)
        device.save()

        doc_url = '{}/{}'.format(device.db_name, example_doc['_id'])

        resp = api.put(doc_url, json=example_doc)
        self.assertEqual(resp.status_code, 201, 'The example document got created')

        import_synced_devices()

        data = get_gather_docs()
        response_id = data[0]['id']

        doc_to_update = api.get(doc_url).json()
        doc_to_update['firstName'] = 'Rey'
        doc_to_update['lastName'] = '(Unknown)'
        resp = api.put(doc_url, json=doc_to_update)
        self.assertEqual(resp.status_code, 201, 'The example document got updated')

        import_synced_devices()

        updated = get_gather_docs()[0]
        self.assertEqual(updated['id'], response_id, 'updated same doc')
        self.assertEqual(updated['data']['_id'], example_doc['_id'], 'updated survey response')
        self.assertEqual(updated['data']['firstName'], 'Rey', 'updated survey response')
        self.assertEqual(updated['data']['lastName'], '(Unknown)', 'updated survey response')

        # check the written meta document
        status = get_meta_doc(device.db_name, example_doc['_id'])
        self.assertEqual(status['last_rev'][0], '2', 'updated meta document')

    def test_document_not_validating(self):
        clean_couch()

        device = DeviceDB(device_id=device_id)
        device.save()

        # post document which is not validating
        doc_url = '{}/{}'.format(device.db_name, example_doc['_id'])
        non_validating_doc = example_doc.copy()
        non_validating_doc.pop('firstName')  # remove required key
        resp = api.put(doc_url, json=non_validating_doc)
        self.assertEqual(resp.status_code, 201, 'The example document got created')

        import_synced_devices()
        data = get_gather_docs()

        if data[0] and data[0]['data']:
            self.assertNotEqual(data[0], example_doc['_id'], 'doc didnt get imported to CouchDB')

        status = get_meta_doc(device.db_name, example_doc['_id'])

        self.assertTrue('error' in status, 'posts error key')
        self.assertFalse('last_rev' in status, 'no last rev key')
        self.assertFalse('gather_id' in status, 'no gather id key')

        self.assertIn('validat', status['error'], 'saves error object')
        self.assertNotIn('JSON serializable', status['error'], 'not error on posting error')

    def test_get_survey_mapping(self):
        clean_couch()
        surveys = []

        # Post 30+ surveys to the gather instance, so it starts paginate
        # then we can see that they get mapped right
        while len(surveys) < 40:
            url = '{}/surveys/'.format(settings.GATHER_CORE_URL)
            survey_name = random_string()[:49]
            example_survey['name'] = survey_name
            requests.post(url, json=example_survey, headers=auth_headers).json()
            surveys.append(survey_name)

        mapping = get_survey_mapping()

        # There's gonna be some fixture surveys etc so more than 40
        self.assertGreater(len(mapping.keys()), len(surveys), 'mapping returns all surveys')

        for survey in surveys:
            self.assertEqual(type(mapping[survey]), int, 'adds a survey id for every key')
