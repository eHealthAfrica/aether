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

from http.cookies import SimpleCookie
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory, override_settings
from django.urls import reverse

from rest_framework import status

from aether.common.multitenancy.tests.fakeapp.models import (
    TestModel,
    TestChildModel,
    TestGrandChildModel,
    TestNoMtModel,
)
from aether.common.multitenancy.tests.fakeapp.serializers import (
    TestModelSerializer,
    TestChildModelSerializer,
)
from aether.common.multitenancy.models import MtInstance
from aether.common.multitenancy import utils

TEST_REALM = 'realm-test'
TEST_REALM_2 = 'realm-test-2'


class MultitenancyTests(TestCase):

    def setUp(self):
        super(MultitenancyTests, self).setUp()
        self.request = RequestFactory().get('/')
        self.request.COOKIES[settings.REALM_COOKIE] = TEST_REALM

        username = 'user'
        email = 'user@example.com'
        password = 'secretsecret'

        user = get_user_model().objects.create_user(username, email, password)
        self.request.user = user
        self.client.cookies = SimpleCookie({settings.REALM_COOKIE: TEST_REALM})
        self.assertTrue(self.client.login(username=username, password=password))

    def test_get_multitenancy_model(self):
        self.assertEqual(settings.MULTITENANCY_MODEL, 'fakeapp.TestModel')
        self.assertEqual(utils.get_multitenancy_model(), TestModel)

    def test_models(self):
        obj1 = TestModel.objects.create(name='one')
        self.assertFalse(obj1.is_accessible(TEST_REALM))
        self.assertTrue(obj1.is_accessible(settings.DEFAULT_REALM))
        self.assertEqual(obj1.get_realm(), settings.DEFAULT_REALM)

        child1 = TestChildModel.objects.create(name='child', parent=obj1)
        self.assertEqual(child1.get_mt_instance(), obj1)
        self.assertFalse(child1.is_accessible(TEST_REALM))
        self.assertTrue(child1.is_accessible(settings.DEFAULT_REALM))
        self.assertEqual(child1.get_realm(), settings.DEFAULT_REALM)

        self.assertTrue(MtInstance.objects.count() == 0)

        obj1.add_to_realm(self.request)

        self.assertTrue(MtInstance.objects.count() > 0)
        self.assertTrue(obj1.is_accessible(TEST_REALM))
        self.assertEqual(obj1.get_realm(), TEST_REALM)
        self.assertTrue(child1.is_accessible(TEST_REALM))
        self.assertEqual(child1.get_realm(), TEST_REALM)

        # grandchildren
        grandchild = TestGrandChildModel.objects.create(name='grandchild', parent=child1)
        self.assertRaises(NotImplementedError, grandchild.get_mt_instance)
        self.assertRaises(NotImplementedError, grandchild.is_accessible, TEST_REALM)
        self.assertRaises(NotImplementedError, grandchild.get_realm)

        realm1 = MtInstance.objects.get(instance=obj1)
        self.assertEqual(str(realm1), str(obj1))
        self.assertEqual(realm1.realm, TEST_REALM)

    def test_serializers(self):
        obj1 = TestModelSerializer(
            data={'name': 'a name'},
            context={'request': self.request},
        )
        self.assertTrue(obj1.is_valid(), obj1.errors)

        # check the user queryset
        self.assertEqual(obj1.fields['user'].get_queryset().count(), 0)
        # we need to add the user to current realm
        utils.add_user_to_realm(self.request, self.request.user)
        self.assertEqual(obj1.fields['user'].get_queryset().count(), 1)

        self.assertTrue(MtInstance.objects.count() == 0)
        obj1.save()
        self.assertTrue(MtInstance.objects.count() > 0)

        realm1 = MtInstance.objects.first()
        self.assertEqual(realm1.instance.pk, obj1.data['id'])
        self.assertEqual(realm1.realm, TEST_REALM)

        # create another TestModel instance
        obj2 = TestModel.objects.create(name='two')
        self.assertFalse(obj2.is_accessible(TEST_REALM))

        child1 = TestChildModelSerializer(context={'request': self.request})
        # obj2 is not in the child1 parent queryset
        self.assertEqual(child1.fields['parent'].get_queryset().count(), 1)
        self.assertEqual(child1.fields['parent'].get_queryset().first().pk, obj1.data['id'])

        # try to save a child with the wrong parent
        child2 = TestChildModelSerializer(
            data={'name': 'child', 'parent': str(obj2.pk)},
            context={'request': self.request},
        )
        self.assertFalse(child2.is_valid(), child2.errors)
        # {'parent': [ErrorDetail(string='Invalid pk "#" - object does not exist.', code='does_not_exist')]
        self.assertEqual(child2.errors['parent'][0].code, 'does_not_exist')
        self.assertEqual(str(child2.errors['parent'][0]), f'Invalid pk "{obj2.pk}" - object does not exist.')

    def test_views(self):
        # create data assigned to different realms
        realm1_group = utils.get_auth_group(self.request)
        obj1 = TestModel.objects.create(name='one')
        child1 = TestChildModel.objects.create(name='child1', parent=obj1)
        obj1.add_to_realm(self.request)
        self.assertEqual(obj1.mt.realm, TEST_REALM)
        user1 = get_user_model().objects.create(username='user1')
        utils.add_user_to_realm(self.request, user1)

        # change realm
        self.request.COOKIES[settings.REALM_COOKIE] = TEST_REALM_2
        realm2_group = utils.get_auth_group(self.request)
        self.assertNotEqual(realm1_group, realm2_group)

        obj2 = TestModel.objects.create(name='two')
        child2 = TestChildModel.objects.create(name='child2', parent=obj2)
        obj2.add_to_realm(self.request)
        self.assertEqual(obj2.mt.realm, TEST_REALM_2)
        user2 = get_user_model().objects.create(username='user2')
        utils.add_user_to_realm(self.request, user2)

        # check users realm groups
        self.assertIn(realm1_group, user1.groups.all())
        self.assertIn(realm2_group, user2.groups.all())
        self.assertEqual(self.request.user.groups.count(), 0)

        self.assertNotIn(realm2_group, user1.groups.all())
        self.assertNotIn(realm1_group, user2.groups.all())

        self.assertEqual(TestModel.objects.count(), 2)
        self.assertEqual(TestChildModel.objects.count(), 2)
        self.assertEqual(get_user_model().objects.count(), 3)

        # check that views only return instances linked to "realm1"
        url = reverse('testmodel-list')
        response = self.client.get(url)
        self.assertEqual(response.client.cookies[settings.REALM_COOKIE].value, TEST_REALM)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        data = response.json()
        self.assertEqual(data['count'], 1)

        # detail endpoint
        url = reverse('testmodel-detail', kwargs={'pk': obj1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        url = reverse('testchildmodel-detail', kwargs={'pk': child1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # is-accessible endpoint
        url = reverse('testmodel-is-accessible', kwargs={'pk': obj1.pk})
        response = self.client.head(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        url = reverse('testchildmodel-is-accessible', kwargs={'pk': child1.pk})
        response = self.client.head(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        url = reverse('testchildmodel-is-accessible', kwargs={'pk': 99})
        response = self.client.head(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # custom endpoint
        url = reverse('testmodel-custom-404', kwargs={'pk': obj1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        url = reverse('testchildmodel-custom-403', kwargs={'pk': child1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        url = reverse('testchildmodel-custom-403', kwargs={'pk': 99})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # users
        url = reverse('user-list')
        response = self.client.get(url)
        data = response.json()
        # only user1 belongs to TEST_REALM,
        # user2 belongs to TEST_REALM_2 and
        # self.request.user belongs to none
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['id'], user1.id, data['results'][0])

        url = reverse('user-detail', kwargs={'pk': user1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # linked to another realm "realm2" *************************************

        # detail endpoint
        url = reverse('testmodel-detail', kwargs={'pk': obj2.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        url = reverse('testchildmodel-detail', kwargs={'pk': child2.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # is-accessible endpoint
        url = reverse('testmodel-is-accessible', kwargs={'pk': obj2.pk})
        response = self.client.head(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        url = reverse('testchildmodel-is-accessible', kwargs={'pk': child2.pk})
        response = self.client.head(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        url = reverse('testchildmodel-is-accessible', kwargs={'pk': 99})
        response = self.client.head(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # custom endpoint
        url = reverse('testmodel-custom-404', kwargs={'pk': obj2.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        url = reverse('testchildmodel-custom-403', kwargs={'pk': child2.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        url = reverse('user-detail', kwargs={'pk': user2.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_current_realm(self):
        request = RequestFactory().get('/')
        self.assertEqual(utils.get_current_realm(request), settings.DEFAULT_REALM)
        request.META[settings.REALM_HEADER] = 'in-headers'
        self.assertEqual(utils.get_current_realm(request), 'in-headers')
        request.COOKIES[settings.REALM_COOKIE] = 'in-cookies'
        self.assertEqual(utils.get_current_realm(request), 'in-cookies')

    def test_is_accessible_by_realm(self):
        # not affected by realm value
        obj2 = TestNoMtModel.objects.create(name='two')
        self.assertTrue(utils.is_accessible_by_realm(self.request, obj2))

        obj1 = TestModel.objects.create(name='one')
        self.assertFalse(utils.is_accessible_by_realm(self.request, obj1))
        self.assertEqual(utils.add_instance_realm_in_headers(obj1, {}),
                         {settings.REALM_COOKIE: settings.DEFAULT_REALM})
        self.assertEqual(utils.add_current_realm_in_headers(self.request, {}),
                         {settings.REALM_COOKIE: TEST_REALM})

        obj1.add_to_realm(self.request)
        self.assertTrue(utils.is_accessible_by_realm(self.request, obj1))
        self.assertEqual(utils.add_instance_realm_in_headers(obj1, {}),
                         {settings.REALM_COOKIE: obj1.mt.realm})

        # change realm
        self.request.COOKIES[settings.REALM_COOKIE] = TEST_REALM_2
        self.assertEqual(obj1.mt.realm, TEST_REALM)
        self.assertEqual(utils.add_instance_realm_in_headers(obj1, {}),
                         {settings.REALM_COOKIE: TEST_REALM})
        self.assertEqual(utils.add_current_realm_in_headers(self.request, {}),
                         {settings.REALM_COOKIE: TEST_REALM_2})
        self.assertFalse(utils.is_accessible_by_realm(self.request, obj1))

        obj1.add_to_realm(self.request)
        self.assertTrue(utils.is_accessible_by_realm(self.request, obj1))
        self.assertEqual(obj1.mt.realm, TEST_REALM_2)
        self.assertEqual(utils.add_instance_realm_in_headers(obj1, {}),
                         {settings.REALM_COOKIE: TEST_REALM_2})

    def test_auth(self):
        realm_group = utils.get_auth_group(self.request)
        self.assertIsNotNone(realm_group)
        self.assertEqual(realm_group.name, utils.get_current_realm(self.request))

        self.assertEqual(self.request.user.groups.count(), 0)
        # it does not complain if the user does not belong to the realm
        utils.remove_user_from_realm(self.request, self.request.user)

        utils.add_user_to_realm(self.request, self.request.user)
        self.assertEqual(self.request.user.groups.count(), 1)
        self.assertIn(realm_group, self.request.user.groups.all())
        utils.remove_user_from_realm(self.request, self.request.user)
        self.assertEqual(self.request.user.groups.count(), 0)
        self.assertNotIn(realm_group, self.request.user.groups.all())

    @override_settings(MULTITENANCY=False)
    def test_no_multitenancy(self, *args):
        obj1 = TestModel.objects.create(name='two')
        self.assertFalse(obj1.is_accessible(TEST_REALM))
        self.assertFalse(obj1.is_accessible(settings.DEFAULT_REALM))
        self.assertIsNone(obj1.get_realm())
        self.assertTrue(MtInstance.objects.count() == 0)

        self.assertTrue(utils.is_accessible_by_realm(self.request, obj1))
        self.assertEqual(utils.add_instance_realm_in_headers(obj1, {}), {})
        self.assertEqual(utils.add_current_realm_in_headers(self.request, {}), {})

        initial_data = TestModel.objects.all()
        self.assertEqual(utils.filter_by_realm(self.request, initial_data), initial_data)

        initial_users = get_user_model().objects.all()
        self.assertEqual(utils.filter_users_by_realm(self.request, initial_users), initial_users)

        obj1.add_to_realm(self.request)
        self.assertTrue(MtInstance.objects.count() == 0)

        self.assertIsNone(utils.get_auth_group(self.request))
        self.assertEqual(self.request.user.groups.count(), 0)
        utils.add_user_to_realm(self.request, self.request.user)
        self.assertEqual(self.request.user.groups.count(), 0)
        utils.remove_user_from_realm(self.request, self.request.user)
        self.assertEqual(self.request.user.groups.count(), 0)
