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

from django.contrib.auth import get_user_model
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import TestCase
from django.test.client import RequestFactory

from ..api.kernel_utils import KernelPropagationError
from ..api.models import Project, Schema
from ..admin import ProjectAdmin, SchemaAdmin


class AdminTest(TestCase):

    def setUp(self):
        # login
        username = 'admin'
        email = 'admin@example.com'
        password = 'adminadmin'
        user = get_user_model().objects.create_superuser(username, email, password)

        self.request = RequestFactory().get('/admin/')
        self.request.user = user
        setattr(self.request, 'session', 'session')
        messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', messages)

    def test__project__actions(self):
        app_admin = ProjectAdmin(Project, AdminSite())

        self.assertEqual(Project.objects.count(), 0)
        with mock.patch('aether.sync.admin.propagate_kernel_project') as mock_propagate:
            app_admin.propagate(self.request, Project.objects.all())
            mock_propagate.assert_not_called()

        Project.objects.create(name='Testing')

        with mock.patch('aether.sync.admin.propagate_kernel_project') as mock_propagate_once:
            app_admin.propagate(self.request, Project.objects.all())
            mock_propagate_once.assert_called_once()

        with mock.patch('aether.sync.admin.propagate_kernel_project',
                        side_effect=KernelPropagationError(':(')) as mock_propagate_err:
            app_admin.propagate(self.request, Project.objects.all())
            mock_propagate_err.assert_called_once()

    def test__schema__actions(self):
        app_admin = SchemaAdmin(Schema, AdminSite())

        self.assertEqual(Schema.objects.count(), 0)
        with mock.patch('aether.sync.admin.propagate_kernel_artefacts') as mock_propagate:
            app_admin.propagate(self.request, Project.objects.all())
            mock_propagate.assert_not_called()

        Schema.objects.create(name='Testing', project=Project.objects.create(name='Testing'))

        with mock.patch('aether.sync.admin.propagate_kernel_artefacts') as mock_propagate_once:
            app_admin.propagate(self.request, Schema.objects.all())
            mock_propagate_once.assert_called_once()

        with mock.patch('aether.sync.admin.propagate_kernel_artefacts',
                        side_effect=KernelPropagationError(':(')) as mock_propagate_err:
            app_admin.propagate(self.request, Schema.objects.all())
            mock_propagate_err.assert_called_once()
