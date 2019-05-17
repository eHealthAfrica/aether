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

from django.contrib.auth import get_user_model
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import TestCase
from django.test.client import RequestFactory

from ..api.utils import PublishError
from ..api.models import Project, Pipeline, Contract
from ..admin import ProjectAdmin, PipelineAdmin, ContractAdmin


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

        with mock.patch('aether.ui.admin.utils.publish_project') as mock_publish:
            app_admin.publish(self.request, Project.objects.all())
            mock_publish.assert_not_called()

        Project.objects.create(name='Testing')

        with mock.patch('aether.ui.admin.utils.publish_project') as mock_publish_once:
            app_admin.publish(self.request, Project.objects.all())
            mock_publish_once.assert_called_once()

        with mock.patch('aether.ui.admin.utils.publish_project',
                        side_effect=PublishError(':(')) as mock_publish_err:
            app_admin.publish(self.request, Project.objects.all())
            mock_publish_err.assert_called_once()

    def test__pipeline__actions(self):
        app_admin = PipelineAdmin(Pipeline, AdminSite())

        self.assertEqual(Pipeline.objects.count(), 0)

        with mock.patch('aether.ui.admin.utils.publish_pipeline') as mock_publish:
            app_admin.publish(self.request, Pipeline.objects.all())
            mock_publish.assert_not_called()

        Pipeline.objects.create(name='Testing', project=Project.objects.create(name='Testing'))

        with mock.patch('aether.ui.admin.utils.publish_pipeline') as mock_publish_once:
            app_admin.publish(self.request, Pipeline.objects.all())
            mock_publish_once.assert_called_once()

        with mock.patch('aether.ui.admin.utils.publish_pipeline',
                        side_effect=PublishError(':(')) as mock_publish_err:
            app_admin.publish(self.request, Pipeline.objects.all())
            mock_publish_err.assert_called_once()

    def test__contract__actions(self):
        app_admin = ContractAdmin(Contract, AdminSite())

        self.assertEqual(Contract.objects.count(), 0)

        with mock.patch('aether.ui.admin.utils.publish_contract') as mock_publish:
            app_admin.publish(self.request, Contract.objects.all())
            mock_publish.assert_not_called()

        Contract.objects.create(
            name='Testing',
            pipeline=Pipeline.objects.create(
                name='Testing',
                project=Project.objects.create(name='Testing'),
            ),
        )

        with mock.patch('aether.ui.admin.utils.publish_contract') as mock_publish_once:
            app_admin.publish(self.request, Contract.objects.all())
            mock_publish_once.assert_called_once()

        with mock.patch('aether.ui.admin.utils.publish_contract',
                        side_effect=PublishError(':(')) as mock_publish_err:
            app_admin.publish(self.request, Contract.objects.all())
            mock_publish_err.assert_called_once()
