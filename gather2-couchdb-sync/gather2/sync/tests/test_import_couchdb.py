import mock
import requests
from django.test import TestCase

from gather2.common.core import utils as core_utils

from ..api.couchdb_helpers import create_db, generate_password as random_string
from ..api.models import DeviceDB
from ..api.tests import clean_couch
from ..couchdb import api as couchdb
from ..import_couchdb import (
    get_meta_doc,
    get_surveys_mapping,
    import_synced_devices,
    post_to_gather,
)


def get_gather_surveys():
    url = core_utils.get_surveys_url()
    return core_utils.get_all_docs(url)


def get_gather_responses(survey_id):
    url = core_utils.get_survey_responses_url(survey_id)
    return core_utils.get_all_docs(url)


headers_testing = core_utils.get_auth_header()
device_id = 'test_import-from-couch'

example_survey = {
    'name': 'example',
    'schema': {
        'title': 'example',
        'properties': {
            'firstName': {
                'type': 'string',
            },
            'lastName': {
                'type': 'string',
            },
        },
        'required': ['firstName', 'lastName'],
    }
}

example_doc = {
    '_id': 'example-aabbbdddccc',
    'deviceId': device_id,
    'firstname': 'Han',
    'lastname': 'Solo'
}

EXAMPLE_MAPPING = {
    "definition": "",
    "revision": 1,
    "project": 1,
    "entities": {
        "Person": 1
    },
    "mapping": [
        ["#!UUID", "Person._id"],
        ["data.village", "Person.villageID"],
        ["data.people[*].name", "Person.name"],
        ["data.people[*].dob", "Person.dob"]
    ]
}


EXAMPLE_SCHEMA = {
    "extends": "http://ehealthafrica.org/#CouchDoc",
    "type": "record",
    "name": "Person",
    "fields": [
        {
            "jsonldPredicate": "@id",
            "type": "string",
            "name": "_id",
            "inherited_from": "http://ehealthafrica.org/#CouchDoc"
        },
        {
            "type": [
                "null",
                "string"
            ],
            "name": "_rev",
            "inherited_from": "http://ehealthafrica.org/#CouchDoc"
        },
        {
            "type": "string",
            "name": "name"
        },
        {
            "type": "string",
            "name": "dob"
        },
        {
            "jsonldPredicate": {
                "_type": "@id",
                "_id": "http://ehealthafrica.org/#Village"
            },
            "type": "string",
            "name": "villageID"
        }
    ]
}

EXAMPLE_SOURCE_DATA = {
    "name": "test",
    "definition": "test",
    "revision": 1,
    "project": 1,
    "data": {
        "village": "somevillageID",
        'deviceId': device_id,
        "people": [
            {
                "name": "PersonA",
                "dob": "2000-01-01"
            },
            {
                "name": "PersonB",
                "dob": "2001-01-01"
            },
            {
                "name": "PersonC",
                "dob": "2002-01-01"
            }
        ]
    }
}

EXAMPLE_REQUIREMENTS = {
    'Person': {
        '_id': ['#!UUID'],
        '_rev': [],
        'name': ['data.people[*].name'],
        'dob': ['data.people[*].dob'],
        'villageID': ['data.village']
        }
}

EXAMPLE_ENTITY = {
  "Person": [
    {
      "_id": "1d119b5d-ca71-4f03-a061-1481e1a694ea",
      "name": "PersonA",
      "dob": "2000-01-01",
      "villageID": "somevillageID"
    },
    {
      "_id": "5474b768-92d9-431f-bf90-3c6db1788109",
      "name": "PersonB",
      "dob": "2001-01-01",
      "villageID": "somevillageID"
    },
    {
      "_id": "64d30f72-c15e-4476-9522-d26cb036c73b",
      "name": "PersonC",
      "dob": "2002-01-01",
      "villageID": "somevillageID"
    }
  ]
}

EXAMPLE_ENTITY_DEFINITION = {'Person': ['_id', '_rev', 'name', 'dob', 'villageID']}

EXAMPLE_FIELD_MAPPINGS = [
    ['#!UUID', 'Person._id'],
    ['data.village', 'Person.villageID'],
    ['data.people[*].name', 'Person.name'],
    ['data.people[*].dob', 'Person.dob']]

        # self.project = models.Project.objects.create(
        #     revision='rev 1',
        #     name='a project name',
        #     salad_schema='a sample salad schema',
        #     jsonld_context='sample context',
        #     rdf_definition='a sample rdf definition'
        # )

        # self.mapping = models.Mapping.objects.create(
        #     name='mapping1',
        #     definition={"sample": "json schema"},
        #     revision='a sample revision field',
        #     project=self.project
        # )

        # self.response = models.Response.objects.create(
        #     revision='a sample revision',
        #     map_revision='a sample map revision',
        #     date=datetime.datetime.now(),
        #     payload={},
        #     mapping=self.mapping
        # )

        # self.schema = models.Schema.objects.create(
        #     name='schema1',
        #     definition={},
        #     revision='a sample revision'
        # )

        # self.projectschema = models.ProjectSchema.objects.create(
        #     name='a project schema name',
        #     mandatory_fields='a sample mandatory fields',
        #     transport_rule='a sample transport rule',
        #     masked_fields='a sample masked field',
        #     is_encrypted=False,
        #     project=self.project,
        #     schema=self.schema
        # )

        # self.entity = models.Entity.objects.create(
        #     revision='a sample revision',
        #     payload={},
        #     status='a sample status',
        #     projectschema=self.projectschema,
        #     response=self.response
        # )

example_survey = EXAMPLE_MAPPING

class ImportTestCase(TestCase):
    def setUp(self):
        clean_couch()
        for survey in get_gather_surveys():
            url = core_utils.get_surveys_url(survey['id'])
            url = survey['url']
            requests.delete(url, headers=headers_testing)

        project = requests.get(
            'http://core-test:9000/projects/demo/',
            headers=headers_testing
        ).json()
        projectschema = requests.get(
            'http://core-test:9000/projectschemas/Person/',
            headers=headers_testing
        ).json()
        # for survey in get_gather_surveys():
        #     url = core_utils.get_surveys_url(survey['id'])
        #     url = survey['url']
        #     requests.delete(url, headers=headers_testing)

        self.assertTrue(core_utils.test_connection())
        url = core_utils.get_surveys_url()

        self.example_survey = {
            'name': 'example',
            'revision': 1,
            'project': project['id'],
            'definition': {
                "mapping": [
                    [
                        "#!uuid",
                        "Person.id"
                    ],
                    [
                        "firstname",
                        "Person.firstName"
                    ],
                    [
                        "lastname",
                        "Person.familyName"
                    ]
                ],
                "entities": {
                    "Person": projectschema['id']
                }
            }
        }
        example_doc['_id'] = 'example-aabbbdddccc'  # reset `_id` changed by tests
        # example_survey['name'] = 'example'  # reset `name` changed by tests

        resp = requests.post(url, json=self.example_survey, headers=headers_testing)

        resp.raise_for_status()
        data = resp.json()
        self.survey_id = data['id']
        self.survey_name = data['name']

    def tearDown(self):
        clean_couch()
        # DANGER: remove ALL created surveys (never test against any PROD server!!!)
        for survey in get_gather_surveys():
            url = core_utils.get_surveys_url(survey['id'])
            url = survey['url']
            requests.delete(url, headers=headers_testing)

    @mock.patch('gather2.sync.import_couchdb.core_utils.test_connection', return_value=False)
    def test_get_surveys_mapping_no_core(self, mock_test):
        self.assertRaises(
            RuntimeError,
            get_surveys_mapping,
        )

    def test_get_surveys_mapping(self):
        survey_names = []

        # Post 30+ surveys to the gather instance, so it starts paginate
        # then we can see that they get mapped right
        while len(survey_names) < 40:
            url = core_utils.get_surveys_url()
            survey_name = random_string()[:49]
            self.example_survey['name'] = survey_name
            response = requests.post(url, json=self.example_survey, headers=headers_testing)
            self.assertEqual(response.status_code, 201, 'The new survey got created')
            survey_names.append(survey_name)

        mapping = get_surveys_mapping()

        # There's gonna be some fixture surveys etc so more than 40
        self.assertGreater(len(mapping.keys()), len(survey_names), 'mapping contains all survey names')

        for survey_name in survey_names:
            self.assertIn(survey_name, mapping)

    @mock.patch('gather2.sync.import_couchdb.core_utils.test_connection', return_value=False)
    def test_post_to_gather_no_core(self, mock_test):
        self.assertRaises(
            RuntimeError,
            post_to_gather,
            document=None,
            mapping=None,
        )

    def test_post_to_gather_non_valid_arguments(self):
        self.assertRaises(
            Exception,
            post_to_gather,
            document={'_id': 'a-b'},
            mapping={},
        )
        self.assertRaises(
            Exception,
            post_to_gather,
            document={'_id': 1},
            mapping={},
        )

    @mock.patch('requests.put')
    @mock.patch('requests.post')
    def test_post_to_gather__without_gather_id(self, mock_post, mock_put):
        post_to_gather(document={'_id': 'a-b'}, mapping={'a': 1}, gather_id=None)
        mock_put.assert_not_called()
        mock_post.assert_called()

    @mock.patch('requests.put')
    @mock.patch('requests.post')
    def test_post_to_gather__with_gather_id(self, mock_post, mock_put):
        post_to_gather(document={'_id': 'a-b'}, mapping={'a': 1}, gather_id=1)
        mock_put.assert_called()
        mock_post.assert_not_called()

    @mock.patch('gather2.sync.import_couchdb.import_synced_docs',
                side_effect=Exception('mocked exception'))
    def test_import_one_document_with_error(self, mock_synced):
        # this creates a test couchdb
        device = DeviceDB(device_id=device_id)
        device.save()
        create_db(device_id)

        resp = couchdb.put('{}/{}'.format(device.db_name, example_doc['_id']), json=example_doc)
        self.assertEqual(resp.status_code, 201, 'The example document got created')

        results = import_synced_devices()
        mock_synced.assert_called()
        self.assertNotEqual(results[0]['error'], None)
        self.assertEqual(results[0]['stats'], None)

    @mock.patch('gather2.sync.import_couchdb.post_to_gather',
                side_effect=Exception('mocked exception'))
    def test_import_one_document_with_with_error_in_core(self, mock_post):
        # this creates a test couchdb
        device = DeviceDB(device_id=device_id)
        device.save()
        create_db(device_id)

        resp = couchdb.put('{}/{}'.format(device.db_name, example_doc['_id']), json=example_doc)
        self.assertEqual(resp.status_code, 201, 'The example document got created')

        results = import_synced_devices()
        mock_post.assert_called()
        self.assertNotEqual(results[0]['error'], None)
        self.assertEqual(results[0]['stats'], None)

    def test_import_one_document(self):
        # this creates a test couchdb
        device = DeviceDB(device_id=device_id)
        device.save()
        create_db(device_id)

        resp = couchdb.put('{}/{}'.format(device.db_name, example_doc['_id']), json=example_doc)
        self.assertEqual(resp.status_code, 201, 'The example document got created')

        # import pdb; pdb.set_trace()
        import_synced_devices()

        data = get_gather_responses(self.survey_id)
        posted = data[0]  # Gather responds with the latest post first

        # import pdb; pdb.set_trace()
        self.assertEqual(
            posted['mapping'],
            self.survey_id,
            'Survey posted to the correct id',
        )
        for key in ['_id', 'firstname', 'lastname']:
            self.assertEqual(posted['payload'].get(key), example_doc.get(key), 'posted example doc')

        # check the written meta document
        status = get_meta_doc(device.db_name, example_doc['_id'])

        self.assertFalse('error' in status, 'no error key')
        self.assertTrue('last_rev' in status, 'last rev key')
        self.assertTrue('gather_id' in status, 'gather id key')

    def test_dont_reimport_document(self):
        # this creates a test couchdb
        device = DeviceDB(device_id=device_id)
        device.save()
        create_db(device_id)

        resp = couchdb.put('{}/{}'.format(device.db_name, example_doc['_id']), json=example_doc)
        self.assertEqual(resp.status_code, 201, 'The example document got created')

        import_synced_devices()

        # reset the user to test the meta doc mechanism
        device.last_synced_seq = 0
        device.save()

        import_synced_devices()

        docs = get_gather_responses(self.survey_id)
        self.assertEqual(len(docs), 1, 'Document is not imported a second time')

    def test_update_document(self):
        # this creates a test couchdb
        device = DeviceDB(device_id=device_id)
        device.save()
        create_db(device_id)

        doc_url = '{}/{}'.format(device.db_name, example_doc['_id'])

        resp = couchdb.put(doc_url, json=example_doc)
        self.assertEqual(resp.status_code, 201, 'The example document got created')

        import_synced_devices()

        docs = get_gather_responses(self.survey_id)
        response_id = docs[0]['id']

        doc_to_update = couchdb.get(doc_url).json()
        doc_to_update['firstname'] = 'Rey'
        doc_to_update['lastname'] = '(Unknown)'
        resp = couchdb.put(doc_url, json=doc_to_update)
        self.assertEqual(resp.status_code, 201, 'The example document got updated')

        import_synced_devices()

        updated = get_gather_responses(self.survey_id)[0]
        self.assertEqual(updated['id'], response_id, 'updated same doc')
        self.assertEqual(updated['payload']['_id'], example_doc['_id'], 'updated survey response')
        self.assertEqual(updated['payload']['firstname'], 'Rey', 'updated survey response')
        self.assertEqual(updated['payload']['lastname'], '(Unknown)', 'updated survey response')

        # check the written meta document
        status = get_meta_doc(device.db_name, example_doc['_id'])
        self.assertEqual(status['last_rev'][0], '2', 'updated meta document')

    def test_document_not_validating(self):
        device = DeviceDB(device_id=device_id)
        device.save()
        create_db(device_id)

        # post document which is not validating
        doc_url = '{}/{}'.format(device.db_name, example_doc['_id'])
        non_validating_doc = example_doc.copy()
        non_validating_doc.pop('firstname')  # remove required key
        resp = couchdb.put(doc_url, json=non_validating_doc)
        self.assertEqual(resp.status_code, 201, 'The example document got created')

        import_synced_devices()
        docs = get_gather_responses(self.survey_id)
        self.assertEqual(len(docs), 0, 'doc did not get imported to gather')
        status = get_meta_doc(device.db_name, example_doc['_id'])

        self.assertTrue('error' in status, 'posts error key')
        self.assertFalse('last_rev' in status, 'no last rev key')
        self.assertFalse('gather_id' in status, 'no gather id key')

        # FIXME: Once error handling in gather-core has been improved, we should
        # be able to uncomment this. See: https://jira.ehealthafrica.org/browse/AET-46
        # self.assertIn('validat', status['error'], 'saves error object')
        # self.assertNotIn('JSON serializable', status['error'], 'not error on posting error')
