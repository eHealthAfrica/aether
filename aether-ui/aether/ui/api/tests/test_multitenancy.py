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

import uuid
import mock

from http.cookies import SimpleCookie

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory, override_settings
from django.urls import reverse

from rest_framework import status

from aether.common.kernel.utils import get_auth_header
from aether.common.multitenancy.models import MtInstance
from aether.common.multitenancy import utils as mt_utils

from .. import models, serializers, utils

CURRENT_REALM = 'realm'
factory = RequestFactory()


class MultitenancyTests(TestCase):

    def setUp(self):
        super(MultitenancyTests, self).setUp()

        self.KERNEL_ID = str(uuid.uuid4())

        self.request = RequestFactory().get('/')
        self.request.COOKIES[settings.REALM_COOKIE] = CURRENT_REALM

        username = 'user'
        email = 'user@example.com'
        password = 'secretsecret'

        user = get_user_model().objects.create_user(username, email, password)
        self.request.user = user
        self.client.cookies = SimpleCookie({settings.REALM_COOKIE: CURRENT_REALM})
        self.assertTrue(self.client.login(username=username, password=password))

        auth_header = get_auth_header()
        self.HEADERS = mt_utils.assign_current_realm_in_headers(self.request, auth_header)

    def tearDown(self):
        self.helper__delete_in_kernel('projects', self.KERNEL_ID)
        self.helper__delete_in_kernel('schemas', self.KERNEL_ID)

        super(MultitenancyTests, self).tearDown()

    def helper__kernel_data(self, *args, **kwargs):
        try:
            return utils.kernel_data_request(*args, **kwargs, headers=self.HEADERS)
        except Exception:
            pass  # ignore

    def helper__delete_in_kernel(self, model, pk):
        self.helper__kernel_data(f'{model}/{pk}/', 'delete')

    def test_get_multitenancy_model(self):
        self.assertEqual(settings.MULTITENANCY_MODEL, 'ui.Project')
        self.assertEqual(mt_utils.get_multitenancy_model(), models.Project)

    def test_models__initial(self):
        project = models.Project.objects.create(name='Project test')
        pipeline = models.Pipeline.objects.create(name='Pipeline test', project=project)
        contract = models.Contract.objects.create(name='Contract test', pipeline=pipeline)

        self.assertFalse(project.is_accessible(CURRENT_REALM))
        self.assertFalse(pipeline.is_accessible(CURRENT_REALM))
        self.assertFalse(contract.is_accessible(CURRENT_REALM))

        self.assertTrue(project.is_accessible(settings.DEFAULT_REALM))
        self.assertTrue(pipeline.is_accessible(settings.DEFAULT_REALM))
        self.assertTrue(contract.is_accessible(settings.DEFAULT_REALM))

        self.assertEqual(project.get_realm(), settings.DEFAULT_REALM)
        self.assertEqual(pipeline.get_realm(), settings.DEFAULT_REALM)
        self.assertEqual(contract.get_realm(), settings.DEFAULT_REALM)

        self.assertTrue(MtInstance.objects.count() == 0)

    def test_models__assign_realm(self):
        project = models.Project.objects.create(name='Project test')
        pipeline = models.Pipeline.objects.create(name='Pipeline test', project=project)
        contract = models.Contract.objects.create(name='Contract test', pipeline=pipeline)

        project.save_mt(self.request)

        self.assertTrue(project.is_accessible(CURRENT_REALM))
        self.assertTrue(pipeline.is_accessible(CURRENT_REALM))
        self.assertTrue(contract.is_accessible(CURRENT_REALM))

        self.assertEqual(project.get_realm(), CURRENT_REALM)
        self.assertEqual(pipeline.get_realm(), CURRENT_REALM)
        self.assertEqual(contract.get_realm(), CURRENT_REALM)

        self.assertTrue(MtInstance.objects.count() > 0)
        mt1 = MtInstance.objects.get(instance=project)
        self.assertEqual(str(mt1), str(project))
        self.assertEqual(mt1.realm, CURRENT_REALM)

        # change realm
        self.request.COOKIES[settings.REALM_COOKIE] = 'another'
        self.assertEqual(project.mt.realm, CURRENT_REALM)
        self.assertFalse(mt_utils.is_accessible_by_realm(self.request, project))

        project.save_mt(self.request)
        self.assertTrue(mt_utils.is_accessible_by_realm(self.request, project))
        self.assertEqual(project.mt.realm, 'another')

    def test_serializers(self):
        obj1 = serializers.ProjectSerializer(
            data={'name': 'a name'},
            context={'request': self.request},
        )
        self.assertTrue(obj1.is_valid(), obj1.errors)

        self.assertTrue(MtInstance.objects.count() == 0)
        obj1.save()
        self.assertTrue(MtInstance.objects.count() > 0, 'sets realm to project')

        mt1 = MtInstance.objects.get(instance__pk=obj1.data['project_id'])
        self.assertEqual(mt1.realm, CURRENT_REALM)

        # create another Project instance
        obj2 = models.Project.objects.create(name='Project 2')
        self.assertFalse(obj2.is_accessible(CURRENT_REALM))

        child1 = serializers.PipelineSerializer(data={}, context={'request': self.request})
        self.assertEqual(child1.fields['project'].get_queryset().count(), 1)
        self.assertEqual(models.Project.objects.count(), 2)

    def test_views(self):
        # create data assigned to different realms
        obj1 = models.Project.objects.create(name='Project 1')
        child1 = models.Pipeline.objects.create(name='Pipeline 1', project=obj1)
        obj1.save_mt(self.request)
        self.assertEqual(obj1.mt.realm, CURRENT_REALM)

        # change realm
        obj2 = models.Project.objects.create(name='Project 1')
        MtInstance.objects.create(instance=obj2, realm='another')
        child2 = models.Pipeline.objects.create(name='Pipeline 2', project=obj2)
        self.assertEqual(obj2.mt.realm, 'another')

        self.assertEqual(models.Project.objects.count(), 2)
        self.assertEqual(models.Pipeline.objects.count(), 2)

        # check that views only return instances linked to CURRENT_REALM
        url = reverse('project-list')
        response = self.client.get(url)
        self.assertEqual(response.client.cookies[settings.REALM_COOKIE].value, CURRENT_REALM)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['count'], 1)

        url = reverse('project-detail', kwargs={'pk': obj1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        url = reverse('pipeline-detail', kwargs={'pk': child1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # linked to another realm
        url = reverse('project-detail', kwargs={'pk': obj2.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        url = reverse('pipeline-detail', kwargs={'pk': child2.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_default_project(self):
        self.assertEqual(models.Project.objects.count(), 0)

        # creates a project
        project = utils.get_default_project(self.request)
        self.assertEqual(project.name, CURRENT_REALM)
        self.assertTrue(project.is_default)
        self.assertEqual(project.get_realm(), CURRENT_REALM)
        self.assertEqual(models.Project.objects.count(), 1)

        # call it a second time does not create a new one
        project_2 = utils.get_default_project(self.request)
        self.assertEqual(project.pk, project_2.pk)
        self.assertEqual(models.Project.objects.count(), 1)

    def test_publish(self):
        project = models.Project.objects.create(name='Project test')
        pipeline = models.Pipeline.objects.create(name='Pipeline test', project=project)
        contract = models.Contract.objects.create(name='Contract test', pipeline=pipeline)

        project.save_mt(self.request)  # assign project to current realm
        project_id = str(project.pk)

        # check headers in kernel request

        with mock.patch('aether.ui.api.utils.kernel_data_request') as mock_kernel:
            utils.publish_project(project)
            mock_kernel.assert_called_once_with(
                url=f'projects/{project_id}/artefacts/',
                method='patch',
                data=mock.ANY,
                headers={
                    settings.REALM_COOKIE: CURRENT_REALM,
                    'Authorization': mock.ANY,
                },
            )

        with mock.patch('aether.ui.api.utils.kernel_data_request') as mock_kernel:
            utils.publish_pipeline(pipeline)
            mock_kernel.assert_called_once_with(
                url=f'projects/{project_id}/artefacts/',
                method='patch',
                data=mock.ANY,
                headers={
                    settings.REALM_COOKIE: CURRENT_REALM,
                    'Authorization': mock.ANY,
                },
            )

        with mock.patch('aether.ui.api.utils.kernel_data_request') as mock_kernel:
            with mock.patch('aether.ui.api.utils.publish_preflight',
                            return_value={}) as mock_preflight:
                utils.publish_contract(contract)
                mock_preflight.assert_called_once()
                mock_kernel.assert_called_once_with(
                    url=f'projects/{project_id}/artefacts/',
                    method='patch',
                    data=mock.ANY,
                    headers={
                        settings.REALM_COOKIE: CURRENT_REALM,
                        'Authorization': mock.ANY,
                    },
                )

    def test__kernel_workflow(self):
        # create a project in kernel and bring it to ui
        url = f'projects/{self.KERNEL_ID}/avro-schemas/'
        artefacts = {
            'name': 'Kernel Project',
            'avro_schemas': [
                {
                    'id': self.KERNEL_ID,
                    'definition': {
                        'name': 'Person',
                        'type': 'record',
                        'fields': [
                            {
                                'name': 'id',
                                'type': 'string',
                            },
                        ],
                    },
                },
            ],
        }
        self.helper__kernel_data(url=url, method='patch', data=artefacts)
        # fetch its artefacts and check
        res = self.helper__kernel_data(url=f'projects/{self.KERNEL_ID}/artefacts/')
        self.assertEqual(
            res,
            {
                'project': self.KERNEL_ID,
                'schemas': [self.KERNEL_ID],
                'project_schemas': [self.KERNEL_ID],
                'mappingsets': [self.KERNEL_ID],
                'mappings': [self.KERNEL_ID],
            }
        )

        self.assertFalse(models.Project.objects.filter(pk=self.KERNEL_ID).exists())

        self.assertEqual(models.Project.objects.count(), 0)
        # bring them to ui
        utils.kernel_artefacts_to_ui_artefacts(self.request)

        self.assertTrue(models.Project.objects.filter(pk=self.KERNEL_ID).exists())
        project = models.Project.objects.get(pk=self.KERNEL_ID)
        self.assertIn('Kernel Project', project.name)

        self.assertEqual(project.pipelines.count(), 1)
        pipeline = project.pipelines.first()

        self.assertEqual(pipeline.contracts.count(), 1)
        contract = pipeline.contracts.first()
        self.assertEqual(
            contract.kernel_refs,
            {
                'entities': {'Person': self.KERNEL_ID},
                'schemas': {'Person': self.KERNEL_ID},
            }
        )

        self.assertEqual(project.get_realm(), CURRENT_REALM)
        self.assertEqual(pipeline.get_realm(), CURRENT_REALM)
        self.assertEqual(contract.get_realm(), CURRENT_REALM)

        self.assertEqual(self.HEADERS, utils.wrap_kernel_headers(project))

        # check publish preflight
        outcome = utils.publish_preflight(contract)
        self.assertEqual(
            outcome,
            {
                'error': ['Contract is read only'],
                'warning': [
                    'Project is already published',
                    'Pipeline (as mapping set) is already published',
                    'Contract (as mapping) is already published',
                    'Entity type "Person" (as schema) is already published',
                    'Entity type "Person" (as project schema) is already published',
                ],
                'info': [],
            }
        )

        # assign project to another realm
        NEW_REALM = 'another'
        self.request.COOKIES[settings.REALM_COOKIE] = NEW_REALM
        project.save_mt(self.request)
        self.assertEqual(project.get_realm(), NEW_REALM)
        self.assertEqual(pipeline.get_realm(), NEW_REALM)
        self.assertEqual(contract.get_realm(), NEW_REALM)

        self.assertNotEqual(self.HEADERS, utils.wrap_kernel_headers(project))

        # check publish preflight again
        outcome = utils.publish_preflight(contract)
        self.assertEqual(
            outcome,
            {
                'error': [
                    'Contract is read only',
                    'Project in kernel belongs to a different tenant',
                ],
                'warning': [],
                'info': [],
            }
        )


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
        obj1 = models.Project.objects.create(name='Project test')
        self.assertFalse(obj1.is_accessible(CURRENT_REALM))
        self.assertTrue(MtInstance.objects.count() == 0)
        self.assertTrue(mt_utils.is_accessible_by_realm(self.request, obj1))

        initial_data = models.Project.objects.all()
        self.assertEqual(mt_utils.filter_by_realm(self.request, initial_data), initial_data)

        self.assertFalse(obj1.save_mt(self.request))
        self.assertTrue(MtInstance.objects.count() == 0)

    def test_models(self):
        obj1 = models.Project.objects.create(name='Project test')
        child1 = models.Pipeline.objects.create(name='Pipeline test', project=obj1)

        self.assertFalse(obj1.is_accessible(CURRENT_REALM))
        self.assertFalse(child1.is_accessible(CURRENT_REALM))

        self.assertFalse(obj1.is_accessible(settings.DEFAULT_REALM))
        self.assertFalse(child1.is_accessible(settings.DEFAULT_REALM))

        self.assertIsNone(obj1.get_realm())
        self.assertIsNone(child1.get_realm())

        self.assertTrue(MtInstance.objects.count() == 0)
        obj1.save_mt(self.request)
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
        models.Project.objects.create(name='Project test')

        child1 = serializers.PipelineSerializer(data={}, context={'request': self.request})
        self.assertEqual(child1.fields['project'].get_queryset().count(), 2)
        self.assertEqual(models.Project.objects.count(), 2)
