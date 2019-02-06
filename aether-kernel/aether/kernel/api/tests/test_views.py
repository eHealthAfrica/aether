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
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import dateutil.parser
import json
import mock
import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from rest_framework import status

from aether.kernel.api import models
from aether.kernel.api.entity_extractor import run_entity_extraction

from . import (
    EXAMPLE_MAPPING,
    EXAMPLE_SCHEMA,
    EXAMPLE_SOURCE_DATA,
    SAMPLE_HOUSEHOLD_DATA,
    SAMPLE_HOUSEHOLD_SCHEMA_DEFINITION,
    SAMPLE_LOCATION_DATA,
    SAMPLE_LOCATION_SCHEMA_DEFINITION,
)


@override_settings(MULTITENANCY=False)
class ViewsTest(TestCase):

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
        )

        self.schema = models.Schema.objects.create(
            name='schema1',
            type='eha.test.schemas',
            family='Person',
            definition=EXAMPLE_SCHEMA,
        )

        self.projectschema = models.ProjectSchema.objects.create(
            name='a project schema name',
            project=self.project,
            schema=self.schema,
        )
        # update the fake value with a real one
        mapping_definition = dict(EXAMPLE_MAPPING)
        mapping_definition['entities']['Person'] = str(self.projectschema.pk)

        self.mappingset = models.MappingSet.objects.create(
            name='a sample mapping set',
            input={},
            schema={},
            project=self.project,
        )

        self.mapping = models.Mapping.objects.create(
            name='mapping1',
            definition=mapping_definition,
            mappingset=self.mappingset,
        )

        self.submission = models.Submission.objects.create(
            payload=EXAMPLE_SOURCE_DATA,
            mappingset=self.mappingset,
            project=self.project,
        )

        # extract entities
        run_entity_extraction(self.submission)
        self.entity = models.Entity.objects.first()

    def tearDown(self):
        self.project.delete()
        self.client.logout()

    def helper_create_object(self, view_name, data, might_fail=False):
        response = self.client.post(reverse(view_name),
                                    json.dumps(data),
                                    content_type='application/json')
        if might_fail:
            self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)
        else:
            self.assertEquals(response.status_code, status.HTTP_201_CREATED, response.content)
        return response

    def test_project_stats_view(self):
        # cleaning data
        models.Submission.objects.all().delete()
        self.assertEqual(models.Submission.objects.count(), 0)
        models.Entity.objects.all().delete()
        self.assertEqual(models.Entity.objects.count(), 0)

        projectschema_2 = models.ProjectSchema.objects.create(
            name='a project schema with stats',
            project=self.project,
            schema=models.Schema.objects.create(
                name='another schema',
                type='eha.test.schemas',
                family=str(self.project.pk),  # identifies passthrough schemas
                definition={
                    'name': 'Person',
                    'type': 'record',
                    'fields': [{'name': 'id', 'type': 'string'}]
                },
                revision='a sample revision',
            ),
        )
        mapping_2 = models.Mapping.objects.create(
            name='a read only mapping with stats',
            definition={
                'entities': {'Person': str(projectschema_2.pk)},
                'mapping': [['#!uuid', 'Person.id']],
            },
            mappingset=self.mappingset,
            is_read_only=True,
        )

        for _ in range(4):
            for __ in range(5):
                # this will also trigger the entities extraction
                # (4 entities per submission -> 3 for self.projectschema + 1 for projectschema_2)
                self.helper_create_object('submission-list', {
                    'payload': EXAMPLE_SOURCE_DATA,
                    'mappingset': str(self.mappingset.pk),
                })

        submissions_count = models.Submission \
                                  .objects \
                                  .filter(mappingset__project=self.project) \
                                  .count()
        self.assertEqual(submissions_count, 20)

        entities_count = models.Entity \
                               .objects \
                               .filter(submission__mappingset__project=self.project) \
                               .count()
        self.assertEqual(entities_count, 80)

        family_person_entities_count = models.Entity \
                                             .objects \
                                             .filter(mapping=self.mapping) \
                                             .count()
        self.assertEqual(family_person_entities_count, 60)

        passthrough_entities_count = models.Entity \
                                           .objects \
                                           .filter(mapping=mapping_2) \
                                           .count()
        self.assertEqual(passthrough_entities_count, 20)

        url = reverse('projects_stats-detail', kwargs={'pk': self.project.pk})
        response = self.client.get(url, format='json')
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        json = response.json()
        self.assertEquals(json['id'], str(self.project.pk))
        self.assertEquals(json['submissions_count'], submissions_count)
        self.assertEquals(json['entities_count'], entities_count)
        self.assertLessEqual(
            dateutil.parser.parse(json['first_submission']),
            dateutil.parser.parse(json['last_submission']),
        )

        # let's try with the family filter
        response = self.client.get(f'{url}?family=Person', format='json')
        json = response.json()
        self.assertEquals(json['submissions_count'], submissions_count)
        self.assertNotEqual(json['entities_count'], entities_count)
        self.assertEquals(json['entities_count'], family_person_entities_count)

        # let's try again but with an unexistent family
        response = self.client.get(f'{url}?family=unknown', format='json')
        json = response.json()
        self.assertEquals(json['submissions_count'], submissions_count)
        self.assertEquals(json['entities_count'], 0, 'No entities in this family')

        # let's try with using the project id
        response = self.client.get(f'{url}?family={str(self.project.pk)}', format='json')
        json = response.json()
        self.assertEquals(json['submissions_count'], submissions_count)
        self.assertNotEqual(json['entities_count'], entities_count)
        self.assertEquals(json['entities_count'], passthrough_entities_count)

        # let's try with the passthrough filter
        response = self.client.get(f'{url}?passthrough=true', format='json')
        json = response.json()
        self.assertEquals(json['submissions_count'], submissions_count)
        self.assertNotEqual(json['entities_count'], entities_count)
        self.assertEquals(json['entities_count'], passthrough_entities_count)

    def test_mapping_set_stats_view(self):
        url = reverse('mappingsets_stats-detail', kwargs={'pk': self.mappingset.pk})
        response = self.client.get(url, format='json')
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        json = response.json()
        self.assertEquals(json['id'], str(self.mappingset.pk))
        submissions_count = models.Submission.objects.filter(mappingset=self.mappingset.pk).count()
        self.assertEquals(json['submissions_count'], submissions_count)
        entities_count = models.Entity.objects.filter(submission__mappingset=self.mappingset.pk).count()
        self.assertEquals(json['entities_count'], entities_count)
        self.assertLessEqual(
            dateutil.parser.parse(json['first_submission']),
            dateutil.parser.parse(json['last_submission']),
        )

    def test_validate_mappings__success(self):
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

    def test_validate_mappings__failure(self):
        '''
        Assert that errors are collected when invalid entities are created.
        '''
        url = reverse('validate-mappings')
        data = json.dumps({
            'submission_payload': EXAMPLE_SOURCE_DATA,
            'mapping_definition': {
                'entities': {
                    'Person': str(self.projectschema),
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
        response = self.client.post(url, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data['entities']), 0, response_data)
        expected = [
            'Could not find schema "person"',
            'No match for path',
            'Expected type "string" at path "Person.dob". Actual value: None',
            'Expected type "string" at path "Person.villageID". Actual value: None',
        ]
        result = [error['description'] for error in response_data['mapping_errors']]
        self.assertEqual(expected, result)

    def test_validate_mappings__400_BAD_REQUEST(self):
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
            },
        })
        response = self.client.post(url, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        self.assertEquals(response.status_code, 400)
        self.assertIn('This field is required', response_data['schemas'][0])
        self.assertIn('This field is required', response_data['submission_payload'][0])

        # try again with wrong schemas
        data = json.dumps({
            'submission_payload': EXAMPLE_SOURCE_DATA,
            'mapping_definition': EXAMPLE_MAPPING,
            # "schemas" must be a dictionary
            'schemas': [],
        })
        response = self.client.post(url, data=data, content_type='application/json')
        response_data = json.loads(response.content)
        self.assertEquals(response.status_code, 400)
        self.assertEquals('Value [] is not an Object', response_data['schemas'][0])

    def test_validate_mappings__500_INTERNAL_SERVER_ERROR(self):
        '''
        Unexpected mapping or extraction failures should return status code 500.
        '''
        with mock.patch('aether.kernel.api.views.validate_mappings') as m:
            m.side_effect = Exception()
            url = reverse('validate-mappings')
            data = json.dumps({
                'submission_payload': EXAMPLE_SOURCE_DATA,
                'mapping_definition': EXAMPLE_MAPPING,
                'schemas': {'Person': EXAMPLE_SCHEMA},
            })
            response = self.client.post(url, data=data, content_type='application/json')
            self.assertEquals(response.status_code, 500)

    # Test resolving linked entities
    def helper_read_linked_data_entities(self, obj, depth):
        url = reverse('entity-detail', kwargs={'pk': obj.pk}) + '?depth=' + str(depth)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        return json.loads(response.content)

    def test_read_linked_data(self):
        location_schema = models.Schema.objects.create(
            name='Location',
            definition=SAMPLE_LOCATION_SCHEMA_DEFINITION,
        )
        household_schema = models.Schema.objects.create(
            name='Household',
            definition=SAMPLE_HOUSEHOLD_SCHEMA_DEFINITION,
        )
        location_projectschema = models.ProjectSchema.objects.create(
            name='Location',
            project=self.project,
            schema=location_schema,
        )
        household_projectschema = models.ProjectSchema.objects.create(
            name='Household',
            project=self.project,
            schema=household_schema,
        )
        location_entity = models.Entity.objects.create(
            payload=SAMPLE_LOCATION_DATA,
            projectschema=location_projectschema,
            status='Publishable',
        )
        household_entity = models.Entity.objects.create(
            payload=SAMPLE_HOUSEHOLD_DATA,
            projectschema=household_projectschema,
            status='Publishable',
        )

        entity_depth_0 = self.helper_read_linked_data_entities(household_entity, 0)
        self.assertEqual(entity_depth_0['resolved'], {})

        entity_depth_2 = self.helper_read_linked_data_entities(household_entity, 2)
        self.assertNotEqual(entity_depth_2['resolved'], {})
        resolved = entity_depth_2['resolved']
        self.assertEqual(resolved['Location'][location_entity.payload['id']]['payload'], location_entity.payload)
        self.assertEqual(resolved['Household'][household_entity.payload['id']]['payload'], household_entity.payload)

        entity_depth_3 = self.helper_read_linked_data_entities(household_entity, 3)
        entity_depth_4 = self.helper_read_linked_data_entities(household_entity, 4)
        self.assertEqual(entity_depth_3, entity_depth_4, 'in case of depth > 3 ... return depth 3')

        entity_two = self.helper_read_linked_data_entities(household_entity, 'two')
        self.assertEqual(entity_depth_0, entity_two, 'in case of depth error... return simple entity')

        entity_neg = self.helper_read_linked_data_entities(household_entity, -1)
        self.assertEqual(entity_depth_0, entity_neg, 'in case of depth<0 ... return simple entity')

    def test_project_artefacts__endpoints(self):
        self.assertEqual(reverse('project-artefacts', kwargs={'pk': 1}), '/projects/1/artefacts/')

        response_get_404 = self.client.get('/projects/artefacts/')
        self.assertEqual(response_get_404.status_code, 404)

        project_id = str(uuid.uuid4())
        url = reverse('project-artefacts', kwargs={'pk': project_id})

        response_get_404 = self.client.get(url)
        self.assertEqual(response_get_404.status_code, 404, 'The project does not exist yet')

        # create project and artefacts
        response_patch = self.client.patch(
            url,
            json.dumps({'name': f'Project {project_id}'}),
            content_type='application/json',
        ).json()
        self.assertEqual(response_patch, {
            'project': project_id,
            'schemas': [],
            'project_schemas': [],
            'mappings': [],
            'mappingsets': [],
        })
        project = models.Project.objects.get(pk=project_id)
        self.assertEqual(project.name, f'Project {project_id}')

        # try to retrieve again
        response_get = self.client.get(url).json()
        self.assertEqual(response_get, {
            'project': project_id,
            'schemas': [],
            'project_schemas': [],
            'mappings': [],
            'mappingsets': [],
        })

    def test_project__avro_schemas__endpoints(self):
        self.assertEqual(reverse('project-avro-schemas', kwargs={'pk': 1}), '/projects/1/avro-schemas/')

        project_id = str(uuid.uuid4())
        url = reverse('project-avro-schemas', kwargs={'pk': project_id})

        # create project and artefacts
        response_patch = self.client.patch(
            url,
            json.dumps({'name': f'Project {project_id}'}),
            content_type='application/json',
        ).json()
        self.assertEqual(response_patch, {
            'project': project_id,
            'schemas': [],
            'project_schemas': [],
            'mappingsets': [],
            'mappings': [],
        })
        project = models.Project.objects.get(pk=project_id)
        self.assertEqual(project.name, f'Project {project_id}')

    def test_schema_validate_definition__success(self):
        url = reverse('schema-list')
        data = json.dumps({
            'name': 'Test',
            'type': 'test',
            'definition': {
                'name': 'Test',
                'type': 'record',
                'fields': [
                    {
                        'name': 'id',
                        'type': 'string'
                    }
                ]
            }
        })
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 201)

        good_complex_schemas = [
            # Has a union type as it's base, but it otherwise ok.
            {
                'name': 'Test-ab',
                'type': 'test',
                'definition': [
                    {
                        'name': 'Test-a',
                        'type': 'record',
                        'aetherBaseSchema': True,
                        'fields': [
                            {
                                'name': 'id',
                                'type': 'string'
                            }
                        ]
                    },
                    {
                        'name': 'AProperty',
                        'type': 'record',
                        'fields': [
                            {
                                'name': 'other_type',
                                'type': 'string'
                            }
                        ]
                    }
                ]
            }
        ]

        for schema in good_complex_schemas:
            response = self.client.post(url, json.dumps(schema), content_type='application/json')
            self.assertEqual(response.status_code, 201)

    def test_schema_validate_definition__errors(self):
        url = reverse('schema-list')
        bad_schemas = [
            {
                'name': 'Test',
                'type': 'test',
                'definition': {
                    'name': 'Test',
                    'type': 'record',
                    'aetherBaseSchema': True,
                    'fields': [
                        # missing field "id"
                        {
                            'name': 'a',
                            'type': 'string'
                        }
                    ]
                }
            },
            {
                'name': 'Test',
                'type': 'test',
                'definition': {
                    'name': 'Test',
                    'type': 'record',
                    'aetherBaseSchema': True,
                    'fields': [
                        {
                            'name': 'id',
                            'type': 'int'  # id is not of type "string"
                        }
                    ]
                }
            }
        ]

        for schema in bad_schemas:
            response = self.client.post(url, json.dumps(schema), content_type='application/json')
            response_content = json.loads(response.content)
            self.assertIn(
                'A schema is required to have a field "id" of type "string"',
                response_content['definition'][0],
            )
            self.assertEqual(response.status_code, 400)

    def test_project__schemas_skeleton(self):
        self.assertEqual(reverse('project-skeleton', kwargs={'pk': 1}),
                         '/projects/1/schemas-skeleton/')
        url = reverse('project-skeleton', kwargs={'pk': self.project.pk})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        json = response.json()
        self.assertEqual(json, {
            'jsonpaths': ['id', '_rev', 'name', 'dob', 'villageID'],
            'docs': {'id': 'ID', '_rev': 'REVISION', 'name': 'NAME', 'villageID': 'VILLAGE'},
            'name': 'a project name-Person',
            'schemas': 1,
        })

        # try with family parameter
        response = self.client.get(f'{url}?family=Person')
        self.assertEquals(response.status_code, 200)
        json = response.json()
        self.assertEqual(json, {
            'jsonpaths': ['id', '_rev', 'name', 'dob', 'villageID'],
            'docs': {'id': 'ID', '_rev': 'REVISION', 'name': 'NAME', 'villageID': 'VILLAGE'},
            'name': 'a project name-Person',
            'schemas': 1,
        })

        response = self.client.get(f'{url}?family=City')
        self.assertEquals(response.status_code, 200)
        json = response.json()
        self.assertEqual(json, {
            'jsonpaths': [],
            'docs': {},
            'name': 'a project name',
            'schemas': 0,
        })

        # try with passthrough parameter
        response = self.client.get(f'{url}?passthrough=true')
        self.assertEquals(response.status_code, 200)
        json = response.json()
        self.assertEqual(json, {
            'jsonpaths': [],
            'docs': {},
            'name': 'a project name',
            'schemas': 0,
        })

        # create and assign passthrough schema
        models.ProjectSchema.objects.create(
            name='a passthrough project schema',
            project=self.project,
            schema=models.Schema.objects.create(
                name='passthrough schema',
                type='eha.test.schemas',
                family=str(self.project.pk),  # identifies passthrough schemas
                definition={
                    'name': 'passthrough',
                    'type': 'record',
                    'fields': [{
                        'name': 'one',
                        'type': 'string',
                    }]
                },
                revision='a sample revision',
            ),
        )
        response = self.client.get(f'{url}?passthrough=true')
        self.assertEquals(response.status_code, 200)
        json = response.json()
        self.assertEqual(json, {
            'jsonpaths': ['one'],
            'docs': {},  # "one" field does not have "doc"
            'name': 'a project name-passthrough',
            'schemas': 1,
        })

    def test_project__schemas_skeleton__no_linked_data(self):
        self.assertEqual(reverse('project-skeleton', kwargs={'pk': 1}),
                         '/projects/1/schemas-skeleton/')

        project = models.Project.objects.create(name='Alone')
        response = self.client.get(reverse('project-skeleton', kwargs={'pk': project.pk}))
        self.assertEquals(response.status_code, 200)
        json = response.json()
        self.assertEqual(json, {
            'jsonpaths': [],
            'docs': {},
            'name': 'Alone',
            'schemas': 0,
        })

        models.ProjectSchema.objects.create(
            name='1st',
            project=project,
            schema=models.Schema.objects.create(name='First', definition={}),
        )
        models.ProjectSchema.objects.create(
            name='2nd',
            project=project,
            schema=models.Schema.objects.create(name='Second', definition={}),
        )
        response = self.client.get(reverse('project-skeleton', kwargs={'pk': project.pk}))
        self.assertEquals(response.status_code, 200)
        json = response.json()
        self.assertEqual(json, {
            'jsonpaths': [],
            'docs': {},
            'name': 'Alone-Second',
            'schemas': 2,
        })

    def test_schema__skeleton(self):
        self.assertEqual(reverse('schema-skeleton', kwargs={'pk': 1}),
                         '/schemas/1/skeleton/')

        response = self.client.get(reverse('schema-skeleton', kwargs={'pk': self.schema.pk}))
        self.assertEquals(response.status_code, 200)
        json = response.json()
        self.assertEqual(json, {
            'jsonpaths': ['id', '_rev', 'name', 'dob', 'villageID'],
            'docs': {'id': 'ID', '_rev': 'REVISION', 'name': 'NAME', 'villageID': 'VILLAGE'},
            'name': 'Person',
        })

    def test_projectschema__skeleton(self):
        self.assertEqual(reverse('projectschema-skeleton', kwargs={'pk': 1}),
                         '/projectschemas/1/skeleton/')

        response = self.client.get(reverse('projectschema-skeleton', kwargs={'pk': self.projectschema.pk}))
        self.assertEquals(response.status_code, 200)
        json = response.json()
        self.assertEqual(json, {
            'jsonpaths': ['id', '_rev', 'name', 'dob', 'villageID'],
            'docs': {'id': 'ID', '_rev': 'REVISION', 'name': 'NAME', 'villageID': 'VILLAGE'},
            'name': 'a project name-Person',
        })

    def test_submission__extract__endpoint(self):
        self.assertEqual(reverse('submission-extract', kwargs={'pk': 1}),
                         '/submissions/1/extract/')
        url = reverse('submission-extract', kwargs={'pk': self.submission.pk})

        models.Entity.objects.all().delete()  # remove all entities
        self.assertEqual(self.submission.entities.count(), 0)
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.payload['aether_errors'], [])

        response = self.client.post(url)
        self.assertEquals(response.status_code, 405, 'only PATCH')

        with mock.patch('aether.kernel.api.views.run_entity_extraction',
                        side_effect=Exception('oops')):
            response = self.client.patch(url)
        self.assertEquals(response.status_code, 400)
        self.assertEqual(self.submission.entities.count(), 0)
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.payload['aether_errors'], ['oops'])

        response = self.client.patch(url)
        self.assertEquals(response.status_code, 200)
        self.assertNotEqual(self.submission.entities.count(), 0)
