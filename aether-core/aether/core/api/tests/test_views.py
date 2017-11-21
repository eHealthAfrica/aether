import json
import datetime

from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from django.urls import reverse

from rest_framework import status
from .. import models

from . import (EXAMPLE_MAPPING, EXAMPLE_SCHEMA, EXAMPLE_SOURCE_DATA)


class ViewsTest(TransactionTestCase):

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
            definition={"sample": "json schema"},
            revision='a sample revision field',
            project=self.project
        )

        self.response = models.Response.objects.create(
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
            payload={},
            status='a sample status',
            projectschema=self.projectschema,
            response=self.response
        )

    def tearDown(self):
        self.client.logout()

    """
    def test_get_object(self):
        client = test.APIClient()
        url = reverse('mapping-detail', kwargs={'name': 'mapping1'})
        # data = {}
        response = client.get(url)
        self.assertEquals(response, 'a sample revision field')
    """

    # TEST CREATE:
    def helper_create_object(self, view_name, data):
        url = reverse(view_name)
        data = json.dumps(data)
        response = self.client.post(url, data, content_type='application/json')
        self.assertEquals(response.status_code, status.HTTP_201_CREATED)

    def test_api_create_instance(self):
        self.helper_create_object('project-list', {
            'name': 'Project name',
            'revision': 'Sample project revision',
            'salad_schema': 'Sample project SALAD schema',
            'jsonld_context': 'Sample JSONLD context',
            'rdf_definition': 'Sample RDF definition'
        })
        self.helper_create_object('mapping-list', {
            'name': 'Mapping name',
            'definition': EXAMPLE_MAPPING,
            'revision': 'Sample mapping revision',
            'project': self.project.pk
        })
        self.helper_create_object('response-list', {
            'revision': 'Sample response revision',
            'map_revision': 'Sample map revision',
            'date': str(datetime.datetime.now()),
            'payload': EXAMPLE_SOURCE_DATA,
            # 'mapping': self.mapping.pk TODO
        })
        self.helper_create_object('schema-list', {
            'name': 'Schema name',
            'type': 'Type',
            'definition': EXAMPLE_SCHEMA,
            'revision': 'a sample revision'
        })
        self.helper_create_object('projectschema-list', {
            'name': 'Project Schema name',
            'mandatory_fields': 'Sample projectschema mandatory fields',
            'transport_rule': 'Sample projectschema transport rule',
            'masked_fields': 'Sample projectschema masked fields',
            'isEncrypted': True,
            'project': self.project.pk,
            'schema': self.schema.pk
        })
        self.helper_create_object('entity-list', {
            'revision': 'Sample entity revision',
            'payload': {},
            'status': 'Publishable',
            'projectschema': self.projectschema.pk,
            'response': str(self.response.pk)
        })

    # TEST READ
    def helper_read_object_id(self, view_name, Obj):
        url = reverse(view_name, kwargs={'pk': Obj.pk})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def helper_read_object_name(self, view_name, Obj):
        url = reverse(view_name, kwargs={'name': Obj.name})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_api_read_instance_name(self):
        self.helper_read_object_name('project-detail', self.project)
        self.helper_read_object_name('mapping-detail', self.mapping)
        self.helper_read_object_name('schema-detail', self.schema)
        self.helper_read_object_name('projectschema-detail', self.projectschema)

    def test_api_read_instance(self):
        self.helper_read_object_id('response-detail', self.response)
        self.helper_read_object_id('entity-detail', self.entity)

    # TEST UPDATE

    def helper_update_object_id(self, view_name, updated_data, Obj):
        url = reverse(view_name, kwargs={'pk': Obj.pk})
        updated_data = json.dumps(updated_data)
        response = self.client.put(url, updated_data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_api_update_instance_id(self):
        self.helper_update_object_id('response-detail', {
            'revision': 'Sample response revision updated',
            'map_revision': 'Sample map revision updated',
            'date': str(datetime.datetime.now()),
            'payload': {},
            'mapping': self.mapping.pk
        }, self.response)
        self.helper_update_object_id('entity-detail', {
            'revision': 'Sample entity revision updated',
            'payload': {},
            'status': 'Publishable',
            'projectschema': self.projectschema.pk
        }, self.entity)

    def helper_update_object_name(self, view_name, updated_data, Obj):
        url = reverse(view_name, kwargs={'name': Obj.name})
        updated_data = json.dumps(updated_data)
        response = self.client.put(url, updated_data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_api_update_instance_name(self):
        self.helper_update_object_name('project-detail', {
            'name': 'Project name 2',
            'revision': 'Sample project revision',
            'salad_schema': 'Sample project SALAD schema',
            'jsonld_context': 'Sample JSONLD context',
            'rdf_definition': 'Sample RDF definition'
        }, self.project)
        self.helper_update_object_name('mapping-detail', {
            'name': 'Mapping name 2',
            'definition': {},
            'revision': 'Sample mapping revision',
            'project': self.project.pk
        }, self.mapping)
        self.helper_update_object_name('schema-detail', {
            'name': 'Schema name 2',
            'type': 'Type',
            'definition': {},
            'revision': 'Sample schema revision',
        }, self.schema)
        self.helper_update_object_name('projectschema-detail', {
            'name': 'Project Schema name 2',
            'mandatory_fields': 'Sample projectschema mandatory fields updated',
            'transport_rule': 'Sample projectschema transport rule',
            'masked_fields': 'Sample projectschema masked fields',
            'isEncrypted': True,
            'project': self.project.pk,
            'schema': self.schema.pk
        }, self.projectschema)

    # TEST DELETE
    def helper_delete_object(self, view_name, Obj):
        url = reverse(view_name, kwargs={'name': Obj.name})
        response = self.client.delete(url, format='json', follow=True)
        self.assertEquals(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_api_delete_project(self):
        self.helper_delete_object('project-detail', self.project)

    def test_api_delete_mapping(self):
        self.helper_delete_object('mapping-detail', self.mapping)

    def test_api_delete_schema(self):
        self.helper_delete_object('schema-detail', self.schema)

    def test_api_delete_projectschema(self):
        self.helper_delete_object('projectschema-detail', self.projectschema)

    def helper_delete_object_pk(self, view_name, Obj):
        url = reverse(view_name, kwargs={'pk': Obj.pk})
        response = self.client.delete(url, format='json', follow=True)
        self.assertEquals(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_api_delete_response(self):
        self.helper_delete_object_pk('response-detail', self.response)

    def test_api_delete_entity(self):
        self.helper_delete_object_pk('entity-detail', self.entity)
