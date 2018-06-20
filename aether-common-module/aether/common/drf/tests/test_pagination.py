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

from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from rest_framework import generics, serializers, status

from ..pagination import CustomPagination

factory = RequestFactory()


class PassThroughSerializer(serializers.BaseSerializer):

    def to_representation(self, item):
        return item


class PaginationTests(TestCase):

    def setUp(self):

        username = 'user'
        email = 'user@example.com'
        password = 'secretsecret'

        self.user = get_user_model().objects.create_user(username, email, password)
        self.assertTrue(self.client.login(username=username, password=password))

        self.count = 10485760
        self.view = generics.ListAPIView.as_view(
            serializer_class=PassThroughSerializer,
            queryset=range(1, self.count + 1),
            pagination_class=CustomPagination,
        )

    def test_default_settings(self):
        request = factory.get('/')
        request.user = self.user
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(dict(response.data), {
            'results': list(range(1, 31)),  # default `page_size` is 30
            'previous': None,
            'next': 'http://testserver/?page=2',
            'count': self.count,
        })

    def test_setting_page_size(self):
        request = factory.get('/', {'page_size': 10})
        request.user = self.user
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(dict(response.data), {
            'results': list(range(1, 11)),
            'previous': None,
            'next': 'http://testserver/?page=2&page_size=10',
            'count': self.count,
        })

    def test_setting_page_size_over_maximum(self):
        request = factory.get('/', {'page_size': 10485760})
        request.user = self.user
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(dict(response.data), {
            'results': list(range(1, 1048576)),  # max `page_size` is 1048575
            'previous': None,
            # parameter value is not updated
            'next': 'http://testserver/?page=2&page_size=10485760',
            'count': self.count,
        })

    def test_setting_page_size_to_zero(self):
        request = factory.get('/', {'page_size': 0})
        request.user = self.user
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(dict(response.data), {
            'results': list(range(1, 31)),  # default `page_size` is 30
            'previous': None,
            # parameter value is not updated
            'next': 'http://testserver/?page=2&page_size=0',
            'count': self.count,
        })
