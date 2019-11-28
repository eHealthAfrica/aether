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

from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test.client import RequestFactory

from ..api.kernel_utils import KernelPropagationError

from ..api.tests import CustomTestCase
from ..api.models import Project, XForm
from ..admin import ProjectAdmin, XFormAdmin


class AdminTests(CustomTestCase):

    def setUp(self):
        super(AdminTests, self).setUp()
        self.helper_create_superuser(login=True)

        self.request = RequestFactory().get('/admin/')
        self.request.user = self.admin
        setattr(self.request, 'session', 'session')
        messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', messages)

        self.project = self.helper_create_project()
        self.PROJECT_ID = self.project.project_id

    def test__project__actions(self):
        app_admin = ProjectAdmin(Project, AdminSite())

        self.assertEqual(Project.objects.count(), 1)

        with mock.patch('aether.odk.admin.propagate_kernel_project') as mock_propagate_once:
            app_admin.propagate(self.request, Project.objects.all())
            mock_propagate_once.assert_called_once()

        with mock.patch('aether.odk.admin.propagate_kernel_project',
                        side_effect=KernelPropagationError(':(')) as mock_propagate_err:
            app_admin.propagate(self.request, Project.objects.all())
            mock_propagate_err.assert_called_once()

        Project.objects.all().delete()
        self.assertEqual(Project.objects.count(), 0)

        with mock.patch('aether.odk.admin.propagate_kernel_project') as mock_propagate:
            app_admin.propagate(self.request, Project.objects.all())
            mock_propagate.assert_not_called()

    def test__xform__actions(self):
        app_admin = XFormAdmin(XForm, AdminSite())

        self.assertEqual(XForm.objects.count(), 0)
        with mock.patch('aether.odk.admin.propagate_kernel_artefacts') as mock_propagate:
            app_admin.propagate(self.request, XForm.objects.all())
            mock_propagate.assert_not_called()

        self.helper_create_xform(project_id=self.PROJECT_ID)

        with mock.patch('aether.odk.admin.propagate_kernel_artefacts') as mock_propagate_once:
            app_admin.propagate(self.request, XForm.objects.all())
            mock_propagate_once.assert_called_once()

        with mock.patch('aether.odk.admin.propagate_kernel_artefacts',
                        side_effect=KernelPropagationError(':(')) as mock_propagate_err:
            app_admin.propagate(self.request, XForm.objects.all())
            mock_propagate_err.assert_called_once()
