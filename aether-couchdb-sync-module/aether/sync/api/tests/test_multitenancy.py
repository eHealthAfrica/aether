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

import mock

from http.cookies import SimpleCookie

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory, override_settings
from django.urls import reverse

from rest_framework import status

from aether.common.kernel.utils import get_kernel_server_url
from aether.common.multitenancy.models import MtInstance
from aether.common.multitenancy import utils

from .. import models, serializers
from ..kernel_utils import __upsert_kernel_artefacts as upsert_kernel
from . import MockResponse

CURRENT_REALM = 'realm'
ANOTHER_REALM = 'another'

_username = 'user'
_email = 'user@example.com'
_password = 'secretsecret'


class MultitenancyTests(TestCase):

    def setUp(self):
        super(MultitenancyTests, self).setUp()

        self.request = RequestFactory().get('/')
        self.request.COOKIES[settings.REALM_COOKIE] = CURRENT_REALM

        user = get_user_model().objects.create_user(_username, _email, _password)
        self.request.user = user
        self.helper__change_cookies_realm(CURRENT_REALM)

    def helper__change_cookies_realm(self, realm):
        self.client.cookies = SimpleCookie({settings.REALM_COOKIE: realm})
        self.assertTrue(self.client.login(username=_username, password=_password))

    def test_get_multitenancy_model(self):
        self.assertEqual(settings.MULTITENANCY_MODEL, 'sync.Project')
        self.assertEqual(utils.get_multitenancy_model(), models.Project)

    def test_models(self):
        # not affected by realm value
        mobile_user = models.MobileUser.objects.create(email='user@example.com')
        self.assertTrue(utils.is_accessible_by_realm(self.request, mobile_user))

        obj1 = models.Project.objects.create(name='p')
        child1 = models.Schema.objects.create(name='s', project=obj1)

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

        mt1 = MtInstance.objects.get(instance__pk=obj1.data['project_id'])
        self.assertEqual(mt1.realm, CURRENT_REALM)

        # create another Project instance
        obj2 = models.Project.objects.create(name='another name')
        self.assertFalse(obj2.is_accessible(CURRENT_REALM))

        child1 = serializers.SchemaSerializer(data={}, context={'request': self.request})
        self.assertEqual(child1.fields['project'].get_queryset().count(), 1)
        self.assertEqual(models.Project.objects.count(), 2)

        user1 = serializers.MobileUserSerializer(
            data={'email': 'test_karl@ehealthnigeria.org'},
            context={'request': self.request},
        )
        self.assertTrue(user1.is_valid(), user1.errors)
        user1.save()
        mobile_user1 = models.MobileUser.objects.get(pk=user1.data['id'])
        self.assertEqual(mobile_user1.groups.count(), 1)
        self.assertEqual(mobile_user1.groups.first().name, CURRENT_REALM)

        mobile_user1.groups.clear()
        user1_upd = serializers.MobileUserSerializer(
            mobile_user1,
            data={},
            partial=True,
            context={'request': self.request},
        )
        self.assertTrue(user1_upd.is_valid(), user1_upd.errors)

        self.assertEqual(mobile_user1.groups.count(), 0)
        user1_upd.save()
        self.assertEqual(mobile_user1.groups.count(), 1)
        self.assertEqual(mobile_user1.groups.first().name, CURRENT_REALM)

    def test_views(self):
        # create data assigned to different realms
        obj1 = models.Project.objects.create(name='one')
        child1 = models.Schema.objects.create(name='child1', project=obj1)
        obj1.add_to_realm(self.request)
        self.assertEqual(obj1.mt.realm, CURRENT_REALM)

        # change realm
        obj2 = models.Project.objects.create(name='two')
        MtInstance.objects.create(instance=obj2, realm='another')
        child2 = models.Schema.objects.create(name='child2', project=obj2)
        self.assertEqual(obj2.mt.realm, 'another')

        self.assertEqual(models.Project.objects.count(), 2)
        self.assertEqual(models.Schema.objects.count(), 2)

        # check that views only return instances linked to CURRENT_REALM
        url = reverse('api:project-list')
        response = self.client.get(url)
        self.assertEqual(response.client.cookies[settings.REALM_COOKIE].value, CURRENT_REALM)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['count'], 1)

        url = reverse('api:project-detail', kwargs={'pk': obj1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        url = reverse('api:schema-detail', kwargs={'pk': child1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # linked to another realm
        url = reverse('api:project-detail', kwargs={'pk': obj2.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        url = reverse('api:schema-detail', kwargs={'pk': child2.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @mock.patch('aether.sync.api.kernel_utils.request',
                return_value=MockResponse(status_code=200))
    @mock.patch('aether.sync.api.kernel_utils.get_auth_header',
                return_value={'Authorization': 'Token ABCDEFGH'})
    def test__upsert_kernel_artefacts(self, mock_auth, mock_patch):
        kernel_url = get_kernel_server_url()

        project = models.Project.objects.create(name='p')
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

    def test_views__mobile_user__lifecycle(self):
        self.assertEqual(models.MobileUser.objects.count(), 0)
        url = reverse('api:mobileuser-list')

        response = self.client.post(url, data={'email': 'test_karl@ehealthnigeria.org'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        self.assertEqual(models.MobileUser.objects.count(), 1)

        user_id = response.json()['id']
        mobile_user = models.MobileUser.objects.get(pk=user_id)
        self.assertEqual(mobile_user.groups.count(), 1)
        self.assertEqual(mobile_user.groups.first().name, CURRENT_REALM)

        # create another user with the same email
        response = self.client.post(url, data={'email': 'test_karl@ehealthnigeria.org'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)
        self.assertEqual(models.MobileUser.objects.count(), 1)

        # change realm
        self.helper__change_cookies_realm(ANOTHER_REALM)

        # create another user with the same email again
        response = self.client.post(url, data={'email': 'test_karl@ehealthnigeria.org'})
        self.assertEqual(response.client.cookies[settings.REALM_COOKIE].value, ANOTHER_REALM)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        self.assertEqual(models.MobileUser.objects.count(), 1)

        user2_id = response.json()['id']
        self.assertEqual(user_id, user2_id)
        self.assertEqual(mobile_user.groups.count(), 2)
        self.assertIn(CURRENT_REALM, mobile_user.groups.values_list('name', flat=True))
        self.assertIn(ANOTHER_REALM, mobile_user.groups.values_list('name', flat=True))

        url_detail = reverse('api:mobileuser-detail', kwargs={'pk': user_id})

        # delete the user
        response = self.client.delete(url_detail)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(models.MobileUser.objects.count(), 1)
        self.assertEqual(mobile_user.groups.count(), 1)
        self.assertEqual(mobile_user.groups.first().name, CURRENT_REALM)

        # back to first realm
        self.helper__change_cookies_realm(CURRENT_REALM)

        # delete the user again
        response = self.client.delete(url_detail)
        self.assertEqual(response.client.cookies[settings.REALM_COOKIE].value, CURRENT_REALM)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)
        self.assertEqual(models.MobileUser.objects.count(), 0)


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
        mobile_user = models.MobileUser.objects.create(email='user@example.com')
        self.assertTrue(utils.is_accessible_by_realm(self.request, mobile_user))

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
        child1 = models.Schema.objects.create(name='s', project=obj1)
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

        child1 = serializers.SchemaSerializer(data={}, context={'request': self.request})
        self.assertEqual(child1.fields['project'].get_queryset().count(), 2)
        self.assertEqual(models.Project.objects.count(), 2)
