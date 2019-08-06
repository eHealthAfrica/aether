# Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
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

from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import RequestFactory, override_settings
from django.urls import reverse

from rest_framework import status

from aether.sdk.multitenancy.models import MtInstance
from aether.sdk.multitenancy import utils
from aether.sdk.unittest import MockResponse

from .. import models, serializers
from ..kernel_utils import (
    get_kernel_url,
    __upsert_kernel_artefacts as upsert_kernel,
)
from ..surveyors_utils import is_granted_surveyor

from . import CustomTestCase

CURRENT_REALM = 'realm'


class MultitenancyTests(CustomTestCase):

    def setUp(self):
        super(MultitenancyTests, self).setUp()

        self.helper_create_superuser()
        self.helper_create_user(login=True)

        self.request = RequestFactory().get('/')
        self.request.COOKIES[settings.REALM_COOKIE] = CURRENT_REALM
        self.request.user = self.user
        self.client.cookies[settings.REALM_COOKIE] = CURRENT_REALM

    def test_get_multitenancy_model(self):
        self.assertEqual(settings.MULTITENANCY_MODEL, 'odk.Project')
        self.assertEqual(utils.get_multitenancy_model(), models.Project)

    def test_models__initial(self):
        xform = self.helper_create_xform(with_media=True)
        project = xform.project
        media_file = xform.media_files.first()

        self.assertFalse(project.is_accessible(CURRENT_REALM))
        self.assertFalse(xform.is_accessible(CURRENT_REALM))
        self.assertFalse(media_file.is_accessible(CURRENT_REALM))

        self.assertTrue(project.is_accessible(settings.DEFAULT_REALM))
        self.assertTrue(xform.is_accessible(settings.DEFAULT_REALM))
        self.assertTrue(media_file.is_accessible(settings.DEFAULT_REALM))

        self.assertEqual(project.get_realm(), settings.DEFAULT_REALM)
        self.assertEqual(xform.get_realm(), settings.DEFAULT_REALM)
        self.assertEqual(media_file.get_realm(), settings.DEFAULT_REALM)

        self.assertTrue(MtInstance.objects.count() == 0)

    def test_models__assign_realm(self):
        xform = self.helper_create_xform(with_media=True)
        project = xform.project
        media_file = xform.media_files.first()

        project.add_to_realm(self.request)

        self.assertTrue(project.is_accessible(CURRENT_REALM))
        self.assertTrue(xform.is_accessible(CURRENT_REALM))
        self.assertTrue(media_file.is_accessible(CURRENT_REALM))

        self.assertEqual(project.get_realm(), CURRENT_REALM)
        self.assertEqual(xform.get_realm(), CURRENT_REALM)
        self.assertEqual(media_file.get_realm(), CURRENT_REALM)

        self.assertTrue(MtInstance.objects.count() > 0)
        mt1 = MtInstance.objects.get(instance=project)
        self.assertEqual(str(mt1), str(project))
        self.assertEqual(mt1.realm, CURRENT_REALM)

        # change realm
        self.request.COOKIES[settings.REALM_COOKIE] = 'another'
        self.assertEqual(project.mt.realm, CURRENT_REALM)
        self.assertFalse(utils.is_accessible_by_realm(self.request, project))

        project.add_to_realm(self.request)
        self.assertTrue(utils.is_accessible_by_realm(self.request, project))
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
        obj2 = self.helper_create_project()
        self.assertFalse(obj2.is_accessible(CURRENT_REALM))

        child1 = serializers.XFormSerializer(data={}, context={'request': self.request})
        self.assertEqual(child1.fields['project'].get_queryset().count(), 1)
        self.assertEqual(models.Project.objects.count(), 2)

        surveyor = serializers.SurveyorSerializer(
            data={'username': 'surveyor', 'password': '~t]:vS3Q>e{2k]CE'},
            context={'request': self.request},
        )
        self.assertTrue(surveyor.is_valid(), surveyor.errors)
        surveyor.save()
        self.assertEqual(surveyor.data['username'], 'surveyor')

        user = get_user_model().objects.get(pk=surveyor.data['id'])
        self.assertTrue(user.groups.filter(name=CURRENT_REALM).exists())
        self.assertEqual(
            user.username, f'{CURRENT_REALM}__surveyor',
            'Surveyor username starts with current realm')

        updated_user = serializers.SurveyorSerializer(
            user,
            data={'username': user.username, 'password': 'wUCK:CQsUd?)Zr93'},
            context={'request': self.request},
        )
        self.assertTrue(updated_user.is_valid(), updated_user.errors)
        updated_user.save()
        self.assertEqual(updated_user.data['id'], surveyor.data['id'])
        self.assertEqual(updated_user.data['username'], 'surveyor')
        user.refresh_from_db()
        self.assertEqual(
            user.username, f'{CURRENT_REALM}__surveyor',
            'Not prepended twice')

    def test_views(self):
        # create data assigned to different realms
        obj1 = self.helper_create_project()
        obj1.add_to_realm(self.request)
        self.assertEqual(obj1.mt.realm, CURRENT_REALM)
        child1 = self.helper_create_xform(project_id=obj1.project_id)

        # change realm
        obj2 = self.helper_create_project()
        MtInstance.objects.create(instance=obj2, realm='another')
        self.assertEqual(obj2.mt.realm, 'another')
        child2 = self.helper_create_xform(project_id=obj2.project_id)

        self.assertEqual(models.Project.objects.count(), 2)
        self.assertEqual(models.XForm.objects.count(), 2)

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
        url = reverse('xform-detail', kwargs={'pk': child1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # linked to another realm
        url = reverse('project-detail', kwargs={'pk': obj2.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        url = reverse('xform-detail', kwargs={'pk': child2.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_is_granted_surveyor(self):
        xform = self.helper_create_xform(with_media=True)
        project = xform.project
        media = xform.media_files.first()

        project.add_to_realm(self.request)

        self.assertEqual(project.surveyors.count(), 0, 'no granted surveyors')
        self.assertEqual(xform.surveyors.count(), 0, 'no granted surveyors')

        self.request.user = self.admin
        utils.add_user_to_realm(self.request, self.admin)
        # realm superusers are not granted surveyors
        self.assertFalse(is_granted_surveyor(self.request, project))
        self.assertFalse(is_granted_surveyor(self.request, xform))
        self.assertFalse(is_granted_surveyor(self.request, media))

        self.request.user = self.user
        utils.add_user_to_realm(self.request, self.user)
        # realm users are not granted surveyors
        self.assertFalse(is_granted_surveyor(self.request, project))
        self.assertFalse(is_granted_surveyor(self.request, xform))
        self.assertFalse(is_granted_surveyor(self.request, media))

        surveyor0 = self.helper_create_surveyor(username='surveyor0')
        self.request.user = surveyor0
        # users must also belong to the realm if there are no granted surveyors
        self.assertFalse(is_granted_surveyor(self.request, project))
        self.assertFalse(is_granted_surveyor(self.request, xform))
        self.assertFalse(is_granted_surveyor(self.request, media))

        utils.add_user_to_realm(self.request, surveyor0)
        # if not granted surveyors all realm surveyors are granted surveyors
        self.assertTrue(is_granted_surveyor(self.request, project))
        self.assertTrue(is_granted_surveyor(self.request, xform))
        self.assertTrue(is_granted_surveyor(self.request, media))

        surveyor1 = self.helper_create_surveyor(username='surveyor1')
        xform.surveyors.add(surveyor1)
        self.assertEqual(xform.surveyors.count(), 1, 'one custom granted surveyor')

        # is in the xform surveyors list but does not belong to the realm
        self.request.user = surveyor1
        self.assertFalse(is_granted_surveyor(self.request, project))
        self.assertFalse(is_granted_surveyor(self.request, xform))
        self.assertFalse(is_granted_surveyor(self.request, media))

        utils.add_user_to_realm(self.request, surveyor1)
        self.assertTrue(is_granted_surveyor(self.request, project), 'project has no surveyors')
        self.assertTrue(is_granted_surveyor(self.request, xform))
        self.assertTrue(is_granted_surveyor(self.request, media))

        self.request.user = surveyor0
        # if granted surveyors not all realm users are surveyors
        self.assertFalse(is_granted_surveyor(self.request, xform))
        self.assertFalse(is_granted_surveyor(self.request, media))

        surveyor2 = self.helper_create_surveyor(username='surveyor2')
        project.surveyors.add(surveyor2)
        self.assertEqual(xform.surveyors.count(), 1, 'one custom granted surveyor')

        self.request.user = surveyor1
        self.assertFalse(is_granted_surveyor(self.request, project))
        self.assertTrue(is_granted_surveyor(self.request, xform))
        self.assertTrue(is_granted_surveyor(self.request, media))

        # is in the project surveyors list but does not belong to the realm
        self.request.user = surveyor2
        self.assertFalse(is_granted_surveyor(self.request, xform))
        self.assertFalse(is_granted_surveyor(self.request, media))

        utils.add_user_to_realm(self.request, surveyor2)
        # realm project surveyors are also xform surveyors
        self.assertTrue(is_granted_surveyor(self.request, xform))
        self.assertTrue(is_granted_surveyor(self.request, media))

        xform.surveyors.clear()
        self.assertEqual(xform.surveyors.count(), 0, 'no custom granted surveyor')

        self.request.user = surveyor1
        self.assertFalse(is_granted_surveyor(self.request, xform))
        self.assertFalse(is_granted_surveyor(self.request, media))

        self.request.user = surveyor2
        # realm project surveyors are also xform surveyors
        self.assertTrue(is_granted_surveyor(self.request, xform))
        self.assertTrue(is_granted_surveyor(self.request, media))

    @mock.patch('aether.odk.api.kernel_utils.request',
                return_value=MockResponse(status_code=200))
    @mock.patch('aether.odk.api.kernel_utils.get_kernel_auth_header',
                return_value={'Authorization': 'Token ABCDEFGH'})
    def test__upsert_kernel_artefacts(self, mock_auth, mock_patch):
        kernel_url = get_kernel_url()

        project = self.helper_create_project()
        project.add_to_realm(self.request)

        self.assertTrue(upsert_kernel(
            project=project,
            artefacts={'avro_schemas': []}
        ))

        mock_auth.assert_called_once()
        mock_patch.assert_called_once_with(
            method='patch',
            url=f'{kernel_url}/projects/{str(project.project_id)}/avro-schemas/',
            json={'avro_schemas': []},
            headers={
                'Authorization': 'Token ABCDEFGH',
                settings.REALM_COOKIE: CURRENT_REALM,
            },
        )


@override_settings(MULTITENANCY=False)
class NoMultitenancyTests(CustomTestCase):

    def setUp(self):
        super(NoMultitenancyTests, self).setUp()

        self.helper_create_user()
        self.request = RequestFactory().get('/')
        self.request.user = self.user

    def test_no_multitenancy(self, *args):
        obj1 = self.helper_create_project()
        self.assertFalse(obj1.is_accessible(CURRENT_REALM))
        self.assertTrue(MtInstance.objects.count() == 0)
        self.assertTrue(utils.is_accessible_by_realm(self.request, obj1))

        initial_data = models.Project.objects.all()
        self.assertEqual(utils.filter_by_realm(self.request, initial_data), initial_data)

        obj1.add_to_realm(self.request)
        self.assertTrue(MtInstance.objects.count() == 0)

    def test_models(self):
        obj1 = self.helper_create_project()
        child1 = self.helper_create_xform(project_id=obj1.project_id)

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
        self.helper_create_project()

        child1 = serializers.XFormSerializer(data={}, context={'request': self.request})
        self.assertEqual(child1.fields['project'].get_queryset().count(), 2)
        self.assertEqual(models.Project.objects.count(), 2)

        surveyor1 = serializers.SurveyorSerializer(
            data={'username': 'surveyor', 'password': '~t]:vS3Q>e{2k]CE'},
            context={'request': self.request},
        )
        self.assertTrue(surveyor1.is_valid(), surveyor1.errors)
        surveyor1.save()
        self.assertEqual(surveyor1.data['username'], 'surveyor')
        user = get_user_model().objects.get(pk=surveyor1.data['id'])
        self.assertEqual(user.username, 'surveyor')
        self.assertEqual(user.groups.count(), 1, 'Belongs only to surveyors group')
