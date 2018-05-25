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
# software distributed under the License is distributed on anx
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import mock

from django.contrib.auth import get_user_model
from django.urls import reverse

from . import CustomTestCase
from ..kernel_replication import KernelReplicationError


class ReplicationViewsTests(CustomTestCase):

    def setUp(self):
        super(ReplicationViewsTests, self).setUp()

        username = 'test'
        email = 'test@example.com'
        password = 'testtest'
        self.user = get_user_model().objects.create_user(username, email, password)
        self.assertTrue(self.client.login(username=username, password=password))

    def tearDown(self):
        super(ReplicationViewsTests, self).tearDown()
        self.client.logout()

    def test__project_replication(self):
        url_404 = reverse('project-replicates', kwargs={'pk': self.helper_create_uuid()})
        response = self.client.patch(url_404)
        self.assertEqual(response.status_code, 404)

        project = self.helper_create_project()
        url = reverse('project-replicates', kwargs={'pk': project.pk})

        with mock.patch('aether.odk.api.views.replicate_project',
                        return_value=True) as mock_repl:
            response = self.client.patch(url)
            self.assertEqual(response.status_code, 200)
            mock_repl.assert_called_once()

        with mock.patch('aether.odk.api.views.replicate_project',
                        side_effect=[KernelReplicationError]) as mock_repl:
            response = self.client.patch(url)
            self.assertEqual(response.status_code, 400)
            mock_repl.assert_called_once()

    def test__xform_replication(self):
        url_404 = reverse('xform-replicates', kwargs={'pk': 0})
        response = self.client.patch(url_404)
        self.assertEqual(response.status_code, 404)

        xform = self.helper_create_xform()
        url = reverse('xform-replicates', kwargs={'pk': xform.pk})

        with mock.patch('aether.odk.api.views.replicate_xform',
                        return_value=True) as mock_repl:
            response = self.client.patch(url)
            self.assertEqual(response.status_code, 200)
            mock_repl.assert_called_once()

        with mock.patch('aether.odk.api.views.replicate_xform',
                        side_effect=[KernelReplicationError]) as mock_repl:
            response = self.client.patch(url)
            self.assertEqual(response.status_code, 400)
            mock_repl.assert_called_once()
