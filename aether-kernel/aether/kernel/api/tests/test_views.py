# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on anx
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import copy
import json
import datetime
import dateutil.parser

import mock

from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from django.urls import reverse

from rest_framework import status

from .. import models, constants, mapping_validation

from . import (EXAMPLE_MAPPING, EXAMPLE_SCHEMA, EXAMPLE_SOURCE_DATA,
               SAMPLE_LOCATION_SCHEMA_DEFINITION, SAMPLE_HOUSEHOLD_SCHEMA_DEFINITION,
               SAMPLE_LOCATION_DATA, SAMPLE_HOUSEHOLD_DATA, EXAMPLE_GAMETOKEN_SCHEMA,
               EXAMPLE_VALID_PAYLOAD, EXAMPLE_SOURCE_DATA_ENTITY, EXAMPLE_INVALID_PAYLOAD)


def assign_mapping_entities(mapping, projectschemas):
    entities = {}
    for projectschema in projectschemas:
        entities[projectschema.schema.definition['name']] = str(projectschema.pk)
    mapping_ = copy.deepcopy(mapping)
    mapping_['entities'] = entities
    return mapping_


class ViewsTest(TransactionTestCase):

    entity_payload = {'name': 'Person name updated'}
    test_schema = None
    test_project_schema = None

    def setUp(self):
        username = 'test'
        email = 'test@example.com'
        password = 'testtest'
        self.user = get_user_model().objects.create_user(username, email, password)
        self.assertTrue(self.client.login(username=username, password=password))

        # Set up test model instances:
        self.project = models.Project.objects.create(
            revision='rev 1',
            name='a project name',
            salad_schema='a sample salad schema',
            jsonld_context='sample context',
            rdf_definition='a sample rdf definition'
        )

        self.schema = models.Schema.objects.create(
            name='schema1',
            definition=EXAMPLE_SCHEMA,
            revision='a sample revision'
        )

        self.projectschema = models.ProjectSchema.objects.create(
            name='a project schema name',
            mandatory_fields='a sample mandatory fields',
            transport_rule='a sample transport rule',
            masked_fields='a sample masked field',
            is_encrypted=False,
            project=self.project,
            schema=self.schema
        )

        mapping_definition = assign_mapping_entities(
            mapping=EXAMPLE_MAPPING,
            projectschemas=[self.projectschema],
        )
        self.mapping = models.Mapping.objects.create(
            name='mapping1',
            definition=mapping_definition,
            revision='a sample revision field',
            project=self.project
        )

        self.submission = models.Submission.objects.create(
            revision='a sample revision',
            map_revision='a sample map revision',
            date=datetime.datetime.now(),
            payload=EXAMPLE_SOURCE_DATA,
            mapping=self.mapping
        )

        self.entity = models.Entity.objects.create(
            revision='a sample revision',
            payload=self.entity_payload,
            status='a sample status',
            projectschema=self.projectschema,
            submission=self.submission
        )

    def tearDown(self):
        self.project.delete()
        self.client.logout()

    def get_count(self, view_name):
        url = reverse(view_name)
        response = self.client.get(url)
        return json.loads(response.content).get('count')

    # TEST CREATE:
    def helper_create_object(self, view_name, data, isNegative=False):
        url = reverse(view_name)
        data = json.dumps(data)
        response = self.client.post(url, data, content_type='application/json')
        if isNegative:
            self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        else:
            self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        return response

    def test_api_create_instance(self):
        self.helper_create_object('project-list', {
            'name': 'Project name',
            'revision': 'Sample project revision',
            'salad_schema': 'Sample project SALAD schema',
            'jsonld_context': 'Sample JSONLD context',
            'rdf_definition': 'Sample RDF definition',
        })
        self.helper_create_object('mapping-list', {
            'name': 'Mapping name',
            'definition': EXAMPLE_MAPPING,
            'revision': 'Sample mapping revision',
            'project': str(self.project.pk),
        })
        self.helper_create_object('submission-list', {
            'revision': 'Sample submission revision',
            'map_revision': 'Sample map revision',
            'date': str(datetime.datetime.now()),
            'payload': EXAMPLE_SOURCE_DATA,
            'mapping': str(self.mapping.pk),
        })
        self.helper_create_object('schema-list', {
            'name': 'Schema name',
            'type': 'Type',
            'definition': EXAMPLE_SCHEMA,
            'revision': 'a sample revision',
        })
        self.helper_create_object('projectschema-list', {
            'name': 'Project Schema name',
            'mandatory_fields': 'Sample projectschema mandatory fields',
            'transport_rule': 'Sample projectschema transport rule',
            'masked_fields': 'Sample projectschema masked fields',
            'isEncrypted': True,
            'project': str(self.project.pk),
            'schema': str(self.schema.pk),
        })
        self.helper_create_object('entity-list', {
            'revision': 'Sample entity revision',
            'payload': EXAMPLE_SOURCE_DATA_ENTITY,
            'status': 'Publishable',
            'projectschema': str(self.projectschema.pk),
            'submission': str(self.submission.pk),
        })
        test_schema_id = json.loads(self.helper_create_object('schema-list', {
            'name': 'GameToken',
            'type': 'record',
            'definition': EXAMPLE_GAMETOKEN_SCHEMA,
            'revision': '1',
        }).content)['id']
        self.test_schema = models.Schema.objects.get(pk=test_schema_id)
        test_project_schema_id = json.loads(self.helper_create_object('projectschema-list', {
            'name': 'Project Schema 2',
            'mandatory_fields': 'Sample projectschema mandatory fields',
            'transport_rule': 'Sample projectschema transport rule',
            'masked_fields': 'Sample projectschema masked fields',
            'isEncrypted': True,
            'project': str(self.project.pk),
            'schema': str(self.test_schema.pk),
        }).content)['id']
        self.test_project_schema = models.ProjectSchema.objects.get(pk=test_project_schema_id)
        self.helper_create_object('entity-list', {
            'revision': '1',
            'payload': EXAMPLE_VALID_PAYLOAD,
            'status': 'Publishable',
            'projectschema': str(self.test_project_schema.pk),
            'submission': str(self.submission.pk),
        })
        self.helper_create_object('entity-list', {
            'revision': '1',
            'payload': EXAMPLE_INVALID_PAYLOAD,
            'status': 'Publishable',
            'projectschema': str(self.test_project_schema.pk),
            'submission': str(self.submission.pk),
        }, True)

    # TEST READ

    def helper_read_object_id(self, view_name, Obj):
        url = reverse(view_name, kwargs={'pk': Obj.pk})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response

    def test_api_read_instance(self):
        self.helper_read_object_id('mapping-detail', self.mapping)
        self.helper_read_object_id('submission-detail', self.submission)
        self.helper_read_object_id('entity-detail', self.entity)
        self.helper_read_object_id('project-detail', self.project)
        self.helper_read_object_id('schema-detail', self.schema)
        self.helper_read_object_id('projectschema-detail', self.projectschema)

    # TEST UPDATE

    def helper_update_object_id(self, view_name, updated_data, Obj, isNegative=False):
        url = reverse(view_name, kwargs={'pk': Obj.pk})
        updated_data = json.dumps(updated_data)
        response = self.client.put(url, updated_data, content_type='application/json')
        if isNegative:
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.status_code)
        else:
            self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        return response

    def test_api_update_instance_id(self):
        self.helper_update_object_id('mapping-detail', {
            'name': 'Mapping name 2',
            'definition': {},
            'revision': 'Sample mapping revision',
            'project': str(self.project.pk)
        }, self.mapping)
        self.helper_update_object_id('submission-detail', {
            'revision': 'Sample submission revision updated',
            'map_revision': 'Sample map revision updated',
            'date': str(datetime.datetime.now()),
            'payload': {},
            'mapping': str(self.mapping.pk),
        }, self.submission)
        updated_example_payload = EXAMPLE_SOURCE_DATA_ENTITY
        updated_example_payload['name'] = 'Person name updated'
        self.helper_update_object_id('entity-detail', {
            'revision': 'Sample entity revision updated',
            'payload': updated_example_payload,
            'status': 'Publishable',
            'projectschema': str(self.projectschema.pk),
        }, self.entity)
        updated_example_payload = EXAMPLE_SOURCE_DATA_ENTITY
        updated_example_payload['name'] = 'Test last name updated'
        updated_example_payload['new_prop'] = 'Test prop updated'
        self.helper_update_object_id('entity-detail', {
            'revision': 'Sample entity revision updated',
            'payload': updated_example_payload,
            'merge': 'first_write_wins',
            'status': 'Publishable',
            'projectschema': str(self.projectschema.pk),
        }, self.entity)
        returned_entity = models.Entity.objects.get(pk=self.entity.pk)
        self.assertEqual(self.entity_payload['name'], returned_entity.payload['name'])
        self.assertIsNotNone(returned_entity.payload['new_prop'])
        updated_example_payload['name'] = 'Test last name updated'
        updated_example_payload['new_prop2'] = 'Test prop updated'
        self.helper_update_object_id('entity-detail', {
            'revision': 'Sample entity revision updated',
            'payload': updated_example_payload,
            'merge': 'last_write_wins',
            'status': 'Publishable',
            'projectschema': str(self.projectschema.pk),
        }, self.entity)
        returned_entity = models.Entity.objects.get(pk=self.entity.pk)
        self.assertNotEqual(self.entity_payload['name'], returned_entity.payload['name'])
        self.assertIsNotNone(returned_entity.payload['new_prop2'])
        invalid_example_payload = dict(EXAMPLE_SOURCE_DATA_ENTITY)
        del invalid_example_payload['villageID']
        self.helper_update_object_id('entity-detail', {
            'revision': 'Sample entity revision updated',
            'payload': invalid_example_payload,
            'status': 'Publishable',
            'projectschema': str(self.projectschema.pk),
        }, self.entity, True)
        self.helper_update_object_id('project-detail', {
            'name': 'Project name 2',
            'revision': 'Sample project revision',
            'salad_schema': 'Sample project SALAD schema',
            'jsonld_context': 'Sample JSONLD context',
            'rdf_definition': 'Sample RDF definition'
        }, self.project)
        self.helper_update_object_id('schema-detail', {
            'name': 'Schema name 2',
            'type': 'Type',
            'definition': EXAMPLE_SCHEMA,
            'revision': 'Sample schema revision',
        }, self.schema)
        self.helper_update_object_id('projectschema-detail', {
            'name': 'Project Schema name 2',
            'mandatory_fields': 'Sample projectschema mandatory fields updated',
            'transport_rule': 'Sample projectschema transport rule',
            'masked_fields': 'Sample projectschema masked fields',
            'isEncrypted': True,
            'project': str(self.project.pk),
            'schema': str(self.schema.pk)
        }, self.projectschema)

    # TEST DELETE

    def helper_delete_object_pk(self, view_name, Obj):
        url = reverse(view_name, kwargs={'pk': Obj.pk})
        response = self.client.delete(url, format='json', follow=True)
        self.assertEquals(response.status_code, status.HTTP_204_NO_CONTENT)
        return response

    def test_api_delete_project(self):
        self.helper_delete_object_pk('project-detail', self.project)

    def test_api_delete_schema(self):
        self.helper_delete_object_pk('schema-detail', self.schema)

    def test_api_delete_projectschema(self):
        self.helper_delete_object_pk('projectschema-detail', self.projectschema)

    def test_api_delete_mapping(self):
        self.helper_delete_object_pk('mapping-detail', self.mapping)

    def test_api_delete_submission(self):
        self.helper_delete_object_pk('submission-detail', self.submission)

    def test_api_delete_entity(self):
        self.helper_delete_object_pk('entity-detail', self.entity)

    def test_api_submission_with_empty_mapping(self):
        mapping = {
            'name': 'Empty mapping',
            'definition': {},
            'revision': 'Sample mapping revision',
            'project': str(self.project.pk),
        }
        mapping_response = self.helper_create_object(
            view_name='mapping-list',
            data=mapping,
        )
        mapping_id = mapping_response.json()['id']
        submission = {
            'mapping': mapping_id,
            'payload': {
                'a': 1
            }
        }
        self.helper_create_object(
            view_name='submission-list',
            data=submission,
        )

    def test_mapping_stats_view(self):
        for _ in range(10):
            self.helper_create_object('submission-list', {
                'revision': 'Sample submission revision',
                'map_revision': 'Sample map revision',
                'date': str(datetime.datetime.now()),
                'payload': EXAMPLE_SOURCE_DATA,
                'mapping': str(self.mapping.pk),
            })
        url = reverse('mappings_stats-detail', kwargs={'pk': self.mapping.pk})
        response = self.client.get(url, format='json')
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        json = response.json()
        self.assertEquals(json['id'], str(self.mapping.pk))
        submission_count = models.Submission.objects.count()
        self.assertEquals(json['submission_count'], submission_count)
        self.assertLessEqual(
            dateutil.parser.parse(json['first_submission']),
            dateutil.parser.parse(json['last_submission']),
        )

    def test_example_entity_extraction__success(self):
        '''
        Assert that valid mappings validate and no errors are accumulated.
        '''
        url = reverse('validate-mappings')
        data = json.dumps({
            'submission_payload': EXAMPLE_SOURCE_DATA,
            'mapping_definition': EXAMPLE_MAPPING,
            'schemas': {'Person': EXAMPLE_SCHEMA},
        })
        response = self.client.post(url, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        self.assertEqual(
            len(response_data['entities']),
            len(EXAMPLE_SOURCE_DATA['data']['people']),
        )
        self.assertEqual(len(response_data['mapping_errors']), 0)

    def test_example_entity_extraction__failure(self):
        '''
        Assert that errors are collected when invalid entities are created.
        '''
        url = reverse('validate-mappings')
        data = json.dumps({
            'submission_payload': EXAMPLE_SOURCE_DATA,
            'mapping_definition': {
                'entities': {
                    'Person': 1,
                },
                'mapping': [
                    ['#!uuid', 'Person.id'],
                    # "person" is not a schema
                    ['data.village', 'person.villageID'],
                    # "not_a_field" is not a field of `Person`
                    ['data.village', 'Person.not_a_field'],
                ],
            },
            'schemas': {
                'Person': EXAMPLE_SCHEMA,
            },
        })
        response = self.client.post(
            url,
            data=data,
            content_type='application/json'
        )
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data['entities']), 0)
        self.assertEqual(len(response_data['mapping_errors']), 3)
        expected = set([
                'Could not find schema "person"',
                'No match for path',
                'Extracted record did not conform to registered schema',
        ])
        result = set([
            error['description'] for error in response_data['mapping_errors']
        ])
        self.assertEqual(expected, result)

    def test_example_entity_extraction__400_BAD_REQUEST(self):
        '''
        Invalid requests should return status code 400.
        '''
        url = reverse('validate-mappings')
        data = json.dumps({
            'mapping_definition': {
                'entities': {
                    'Person': 1,
                },
                'mapping': [
                    ['#!uuid', 'Person.id'],
                    # "person" is not a schema
                    ['data.village', 'person.villageID'],
                    # "not_a_field" is not a field of `Person`
                    ['data.village', 'Person.not_a_field'],
                ],
                # "schemas" are missing
            },
        })
        response = self.client.post(
            url,
            data=data,
            content_type='application/json'
        )
        response_data = json.loads(response.content)
        self.assertEquals(response.status_code, 400)
        self.assertIn('This field is required', response_data['schemas'][0])
        self.assertIn('This field is required', response_data['submission_payload'][0])

    def test_example_entity_extraction__500_INTERNAL_SERVER_ERROR(self):
        '''
        Unexpected mapping or extraction failures should return status code 500.
        '''
        with mock.patch('aether.kernel.api.mapping_validation.validate_mappings') as m:
            message = 'test'
            m.side_effect = Exception(message)
            url = reverse('validate-mappings')
            data = json.dumps({
                'submission_payload': EXAMPLE_SOURCE_DATA,
                'mapping_definition': EXAMPLE_MAPPING,
                'schemas': {'Person': EXAMPLE_SCHEMA},
            })
            response = self.client.post(url, data=data, content_type='application/json')
            response_data = json.loads(response.content)
            self.assertEquals(response.status_code, 500)
            self.assertEquals(response_data, message)

    # Test resolving linked entities
    def helper_read_linked_data_entities(self, view_name, obj, depth):
        url = reverse(view_name, kwargs={'pk': obj.pk}) + '?depth=' + str(depth)
        response = self.client.get(url, format='json')
        try:
            int(depth)
            if depth > constants.LINKED_DATA_MAX_DEPTH:
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            else:
                self.assertEqual(response.status_code, status.HTTP_200_OK)
        except Exception as e:
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        return response

    def test_read_linked_data(self):
        location_schema = models.Schema.objects.create(
            name='Location',
            definition=SAMPLE_LOCATION_SCHEMA_DEFINITION,
            revision='1'
        )
        household_schema = models.Schema.objects.create(
            name='Household',
            definition=SAMPLE_HOUSEHOLD_SCHEMA_DEFINITION,
            revision='1'
        )
        location_projectschema = models.ProjectSchema.objects.create(
            name='Location',
            mandatory_fields=[],
            transport_rule=[],
            masked_fields=[],
            is_encrypted=False,
            project=self.project,
            schema=location_schema
        )
        household_projectschema = models.ProjectSchema.objects.create(
            name='Household',
            mandatory_fields=[],
            transport_rule=[],
            masked_fields=[],
            is_encrypted=False,
            project=self.project,
            schema=household_schema
        )
        location_entity = models.Entity.objects.create(
            payload=SAMPLE_LOCATION_DATA,
            projectschema=location_projectschema
        )
        household_entity = models.Entity.objects.create(
            payload=SAMPLE_HOUSEHOLD_DATA,
            projectschema=household_projectschema
        )
        linked_entity = self.helper_read_linked_data_entities('entity-detail', household_entity, 2)
        self.helper_read_linked_data_entities('entity-detail', household_entity, 4)
        self.helper_read_linked_data_entities('entity-detail', household_entity, 'two')
        self.assertIsNotNone(
            json.loads(linked_entity.content)['resolved']
            [location_schema.name][location_entity.payload['id']])

    def test_api_no_cascade_delete_on_entity(self):
        self.helper_delete_object_pk('schema-detail', self.schema)
        modified_entity = models.Entity.objects.get(pk=self.entity.pk)
        self.assertIsNone(modified_entity.projectschema)
        # Test updating entity without a projectschema
        self.helper_update_object_id('entity-detail', {
            'revision': modified_entity.revision,
            'payload': modified_entity.payload,
            'status': 'Publishable',
            'projectschema': None
        }, modified_entity, True)

    def test_custom_viewset(self):
        self.assertNotEqual(reverse('project-list'), reverse('project-fetch'))
        self.assertEqual(reverse('project-fetch'), '/projects/fetch/')

        self.assertNotEqual(reverse('project-detail', kwargs={'pk': 1}),
                            reverse('project-details', kwargs={'pk': 1}))
        self.assertEqual(reverse('project-details', kwargs={'pk': 1}), '/projects/1/details/')

        project_id = str(self.project.pk)

        response_get = self.client.get(reverse('project-list')).json()
        response_post = self.client.post(reverse('project-fetch')).json()

        self.assertEqual(response_get, response_post, 'same detail view')
        self.assertEqual(len(response_get['results']), 1)
        self.assertEqual(response_get['results'][0]['id'], project_id)

        response_get = self.client.get(reverse('project-detail', kwargs={'pk': project_id})).json()
        response_post = self.client.post(reverse('project-details', kwargs={'pk': project_id})).json()

        self.assertEqual(response_get, response_post, 'same list view')
        self.assertEqual(response_get['id'], project_id)
