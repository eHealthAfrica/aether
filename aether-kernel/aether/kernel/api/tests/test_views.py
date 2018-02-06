import json
import datetime
import dateutil.parser

from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from django.urls import reverse

from rest_framework import status
from .. import models

from . import (EXAMPLE_MAPPING, EXAMPLE_SCHEMA, EXAMPLE_SOURCE_DATA)


class ViewsTest(TransactionTestCase):

    entity_payload = {'firstname': 'test first name', 'lastname': 'test last name'}

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

        self.mapping = models.Mapping.objects.create(
            name='mapping1',
            definition={'sample': 'json schema'},
            revision='a sample revision field',
            project=self.project
        )

        self.submission = models.Submission.objects.create(
            revision='a sample revision',
            map_revision='a sample map revision',
            date=datetime.datetime.now(),
            payload={},
            mapping=self.mapping
        )

        self.schema = models.Schema.objects.create(
            name='schema1',
            definition={},
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
    def helper_create_object(self, view_name, data):
        url = reverse(view_name)
        pre_submission_count = self.get_count(view_name)
        data = json.dumps(data)
        response = self.client.post(url, data, content_type='application/json')
        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        post_submission_count = self.get_count(view_name)
        self.assertEquals(post_submission_count, pre_submission_count + 1)
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
            'payload': {},
            'status': 'Publishable',
            'projectschema': str(self.projectschema.pk),
            'submission': str(self.submission.pk),
        })

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

    def helper_update_object_id(self, view_name, updated_data, Obj):
        url = reverse(view_name, kwargs={'pk': Obj.pk})
        updated_data = json.dumps(updated_data)
        response = self.client.put(url, updated_data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
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
        self.helper_update_object_id('entity-detail', {
            'revision': 'Sample entity revision updated',
            'payload': {'firstname': 'Test first name updated'},
            'status': 'Publishable',
            'projectschema': str(self.projectschema.pk),
        }, self.entity)
        self.helper_update_object_id('entity-detail', {
            'revision': 'Sample entity revision updated',
            'payload': {'lastname': 'Test last name updated', 'new_prop': 'Test prop updated'},
            'merge': 'first_write_wins',
            'status': 'Publishable',
            'projectschema': str(self.projectschema.pk),
        }, self.entity)
        self.assertEqual(self.entity_payload['lastname'], self.entity.payload['lastname'])
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
            'definition': {},
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
