# Copyright (C) 2023 by eHealth Africa : http://www.eHealthAfrica.org
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

import json
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory, override_settings
from django.urls import reverse

from rest_framework import status

from aether.sdk.multitenancy.models import MtInstance
from aether.sdk.multitenancy import utils

from .. import models, serializers

CURRENT_REALM = 'realm'


class MultitenancyTests(TestCase):

    def setUp(self):
        super(MultitenancyTests, self).setUp()

        self.request = RequestFactory().get('/')
        self.request.COOKIES[settings.REALM_COOKIE] = CURRENT_REALM

        username = 'user'
        email = 'user@example.com'
        password = 'secretsecret'

        user = get_user_model().objects.create_user(username, email, password)
        self.request.user = user
        self.assertTrue(self.client.login(username=username, password=password))
        self.client.cookies[settings.REALM_COOKIE] = CURRENT_REALM

    def test_get_multitenancy_model(self):
        self.assertEqual(settings.MULTITENANCY_MODEL, 'kernel.Project')
        self.assertEqual(utils.get_multitenancy_model(), models.Project)

    def test_models(self):
        # not affected by realm value
        schema = models.Schema.objects.create(name='schema', definition={})
        self.assertTrue(utils.is_accessible_by_realm(self.request, schema))

        obj1 = models.Project.objects.create(name='p')
        child1 = models.MappingSet.objects.create(name='ms', project=obj1)

        self.assertFalse(obj1.is_accessible(CURRENT_REALM))
        self.assertFalse(child1.is_accessible(CURRENT_REALM))

        self.assertTrue(obj1.is_accessible(settings.DEFAULT_REALM))
        self.assertTrue(child1.is_accessible(settings.DEFAULT_REALM))
        self.assertEqual(obj1.get_realm(), settings.DEFAULT_REALM)
        self.assertEqual(child1.get_realm(), settings.DEFAULT_REALM)

        self.assertTrue(MtInstance.objects.count() == 0)
        obj1.add_to_realm(self.request)
        self.assertTrue(MtInstance.objects.count() > 0)

        self.assertTrue(obj1.is_accessible(CURRENT_REALM))
        self.assertTrue(child1.is_accessible(CURRENT_REALM))
        self.assertEqual(obj1.get_realm(), CURRENT_REALM)
        self.assertEqual(child1.get_realm(), CURRENT_REALM)

        self.assertFalse(obj1.is_accessible(settings.DEFAULT_REALM))
        self.assertFalse(child1.is_accessible(settings.DEFAULT_REALM))

        mt1 = MtInstance.objects.get(instance=obj1)
        self.assertEqual(str(mt1), str(obj1))
        self.assertEqual(mt1.realm, CURRENT_REALM)

        # change realm
        self.request.COOKIES[settings.REALM_COOKIE] = 'another'
        self.assertEqual(obj1.mt.realm, CURRENT_REALM)
        self.assertFalse(utils.is_accessible_by_realm(self.request, obj1))

        obj1.add_to_realm(self.request)
        self.assertTrue(utils.is_accessible_by_realm(self.request, obj1))
        self.assertEqual(obj1.mt.realm, 'another')

    def test_serializers(self):
        obj1 = serializers.ProjectSerializer(
            data={'name': 'a name'},
            context={'request': self.request},
        )
        self.assertTrue(obj1.is_valid(), obj1.errors)

        self.assertTrue(MtInstance.objects.count() == 0)
        obj1.save()
        self.assertTrue(MtInstance.objects.count() > 0, 'sets realm to project')

        mt1 = MtInstance.objects.get(instance__pk=obj1.data['id'])
        self.assertEqual(mt1.realm, CURRENT_REALM)

        # create another Project instance
        obj2 = models.Project.objects.create(name='another name')
        self.assertFalse(obj2.is_accessible(CURRENT_REALM))

        child1 = serializers.MappingSetSerializer(data={}, context={'request': self.request})
        self.assertEqual(child1.fields['project'].get_queryset().count(), 1)
        self.assertEqual(models.Project.objects.count(), 2)

    def test_views(self):
        # create data assigned to different realms
        _simple_schema = {
            'name': 'Perf',
            'type': 'record',
            'fields': [
                {
                    'name': 'id',
                    'type': 'string'
                },
                {
                    'name': 'body',
                    'type': [
                        'null',
                        'string'
                    ]
                }
            ]
        }
        _simple_mapping = {'mapping': [], 'entities': {}}

        obj1 = models.Project.objects.create(name='one')
        child1 = models.MappingSet.objects.create(name='child1', project=obj1)
        obj1.add_to_realm(self.request)
        schema1 = models.Schema.objects.create(name='schema1', definition=_simple_schema)
        schemadecorator1 = models.SchemaDecorator.objects.create(name='sd1', project=obj1, schema=schema1)
        self.assertEqual(obj1.mt.realm, CURRENT_REALM)

        # change realm
        obj2 = models.Project.objects.create(name='two')
        MtInstance.objects.create(instance=obj2, realm='another')
        child2 = models.MappingSet.objects.create(name='child2', project=obj2)
        schema2 = models.Schema.objects.create(name='schema2', definition=_simple_schema)
        schemadecorator2 = models.SchemaDecorator.objects.create(name='sd2', project=obj2, schema=schema2)
        self.assertEqual(obj2.mt.realm, 'another')

        # second project in original realm
        obj1a = models.Project.objects.create(name='1a')
        MtInstance.objects.create(instance=obj1a, realm=CURRENT_REALM)
        child1a = models.MappingSet.objects.create(name='child1a', project=obj1a)
        mapping1a = models.Mapping.objects.create(
            name='mapping1a', mappingset=child1a, definition=_simple_mapping
        )
        self.assertEqual(obj1a.mt.realm, CURRENT_REALM)

        self.assertEqual(models.Project.objects.count(), 3)
        self.assertEqual(models.MappingSet.objects.count(), 3)

        # check that views only return instances linked to CURRENT_REALM
        url = reverse('project-list')
        response = self.client.get(url)
        self.assertEqual(response.client.cookies[settings.REALM_COOKIE].value, CURRENT_REALM)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['count'], 2)

        url = reverse('project-detail', kwargs={'pk': obj1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        url = reverse('mappingset-detail', kwargs={'pk': child1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # linked to another realm
        url = reverse('project-detail', kwargs={'pk': obj2.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # custom endpoints
        url = reverse('project-artefacts', kwargs={'pk': obj2.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        url = reverse('mappingset-detail', kwargs={'pk': child2.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # schema endpoint
        url = reverse('api_schema', kwargs={'version': 'v1'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # try to create an entity linked to a project that belongs to this realm
        entity_data_1 = {
            'schemadecorator': str(schemadecorator2.pk),
            'name': 'playing with realms',
            'status': 'Pending Approval',
            'payload': {
                'id': str(obj1.pk),
            }
        }
        response = self.client.post(
            reverse('entity-list'),
            json.dumps(entity_data_1),
            content_type='application/json'
        )
        # SD2 Does not exists on Realm1
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.json())
        data = response.json()
        self.assertIn('schemadecorator', data)
        self.assertEqual(
            data['schemadecorator'],
            [f'Invalid pk "{str(schemadecorator2.pk)}" - object does not exist.'],
        )
        # Correct Realm, but add bad mapping-set id
        entity_data_1['schemadecorator'] = str(schemadecorator1.pk)
        entity_data_1['mapping'] = str(mapping1a.pk)
        response = self.client.post(
            reverse('entity-list'),
            json.dumps(entity_data_1),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.json())
        # Correct Realm, no bad artifacts
        del entity_data_1['mapping']
        response = self.client.post(
            reverse('entity-list'),
            json.dumps(entity_data_1),
            content_type='application/json'
        )
        # Correct Realm
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())
        entity_1 = response.json()['id']

        # try to assign entity 1 to a project that belongs to another realm
        response = self.client.patch(
            reverse('entity-detail', kwargs={'pk': entity_1}),
            json.dumps({'project': str(obj2.pk)}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn('project', data)
        self.assertEqual(
            data['project'],
            [f'Invalid pk "{str(obj2.pk)}" - object does not exist.'],
        )

        # try to create an entity linked to a project that belongs to another realm
        entity_data_2 = {
            'project': str(obj2.pk),
            'name': 'playing with realms',
            'status': 'Pending Approval',
            'payload': {
                'id': str(obj2.pk),
            }
        }
        response = self.client.post(
            reverse('entity-list'),
            json.dumps(entity_data_2),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn('project', data)
        self.assertEqual(
            data['project'],
            [f'Invalid pk "{str(obj2.pk)}" - object does not exist.'],
        )

    def test_views__project(self):
        url = reverse('project-list')
        response = self.client.post(
            url,
            json.dumps({'name': 'Project new'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        project = models.Project.objects.get(pk=response.json()['id'])
        self.assertTrue(project.is_accessible(CURRENT_REALM))

        project_id = str(uuid.uuid4())
        url = reverse('project-artefacts', kwargs={'pk': project_id})
        self.client.patch(
            url,
            json.dumps({'name': f'Project {project_id}'}),
            content_type='application/json',
        )
        project = models.Project.objects.get(pk=project_id)
        self.assertTrue(project.is_accessible(CURRENT_REALM))

        project_id = str(uuid.uuid4())
        url = reverse('project-avro-schemas', kwargs={'pk': project_id})
        self.client.patch(
            url,
            json.dumps({'name': f'Project {project_id}'}),
            content_type='application/json',
        )
        project = models.Project.objects.get(pk=project_id)
        self.assertTrue(project.is_accessible(CURRENT_REALM))


@override_settings(MULTITENANCY=False)
class NoMultitenancyTests(TestCase):

    def setUp(self):
        super(NoMultitenancyTests, self).setUp()

        self.request = RequestFactory().get('/')

        username = 'user'
        email = 'user@example.com'
        password = 'secretsecret'

        user = get_user_model().objects.create_user(username, email, password)
        self.request.user = user
        self.assertTrue(self.client.login(username=username, password=password))

    def test_no_multitenancy(self, *args):
        # not affected by realm value
        schema = models.Schema.objects.create(name='schema', definition={})
        self.assertTrue(utils.is_accessible_by_realm(self.request, schema))

        project = models.Project.objects.create(name='name')
        self.assertFalse(project.is_accessible(CURRENT_REALM))
        self.assertTrue(MtInstance.objects.count() == 0)
        self.assertTrue(utils.is_accessible_by_realm(self.request, project))

        initial_data = models.Project.objects.all()
        self.assertEqual(utils.filter_by_realm(self.request, initial_data), initial_data)

        project.add_to_realm(self.request)
        self.assertTrue(MtInstance.objects.count() == 0)

    def test_models(self):
        obj1 = models.Project.objects.create(name='p')
        child1 = models.MappingSet.objects.create(name='ms', project=obj1)

        self.assertFalse(obj1.is_accessible(CURRENT_REALM))
        self.assertFalse(child1.is_accessible(CURRENT_REALM))

        self.assertFalse(obj1.is_accessible(settings.DEFAULT_REALM))
        self.assertFalse(child1.is_accessible(settings.DEFAULT_REALM))

        self.assertIsNone(obj1.get_realm())
        self.assertIsNone(child1.get_realm())

        self.assertTrue(MtInstance.objects.count() == 0)
        obj1.add_to_realm(self.request)
        self.assertTrue(MtInstance.objects.count() == 0)

    def test_serializers(self):
        obj1 = serializers.ProjectSerializer(
            data={'name': 'a name'},
            context={'request': self.request},
        )
        self.assertTrue(obj1.is_valid(), obj1.errors)

        self.assertTrue(MtInstance.objects.count() == 0)
        obj1.save()
        self.assertTrue(MtInstance.objects.count() == 0)

        # create another Project instance
        models.Project.objects.create(name='another name')

        child1 = serializers.MappingSetSerializer(data={}, context={'request': self.request})
        self.assertEqual(child1.fields['project'].get_queryset().count(), 2)
        self.assertEqual(models.Project.objects.count(), 2)

    def test_views__project(self):
        url = reverse('project-list')
        response = self.client.post(
            url,
            json.dumps({'name': 'Project new'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        project = models.Project.objects.get(pk=response.json()['id'])
        self.assertFalse(project.is_accessible(CURRENT_REALM))

        project_id = str(uuid.uuid4())
        url = reverse('project-artefacts', kwargs={'pk': project_id})
        self.client.patch(
            url,
            json.dumps({'name': f'Project {project_id}'}),
            content_type='application/json',
        )
        project = models.Project.objects.get(pk=project_id)
        self.assertFalse(project.is_accessible(CURRENT_REALM))

        project_id = str(uuid.uuid4())
        url = reverse('project-avro-schemas', kwargs={'pk': project_id})
        self.client.patch(
            url,
            json.dumps({'name': f'Project {project_id}'}),
            content_type='application/json',
        )
        project = models.Project.objects.get(pk=project_id)
        self.assertFalse(project.is_accessible(CURRENT_REALM))
