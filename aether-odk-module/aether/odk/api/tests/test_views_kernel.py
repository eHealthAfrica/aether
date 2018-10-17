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

import json
import mock

from django.contrib.auth import get_user_model
from django.urls import reverse

from . import CustomTestCase
from ..kernel_utils import KernelPropagationError


class KernelViewsTests(CustomTestCase):

    def setUp(self):
        super(KernelViewsTests, self).setUp()

        username = 'test'
        email = 'test@example.com'
        password = 'testtest'
        self.user = get_user_model().objects.create_user(username, email, password)
        self.assertTrue(self.client.login(username=username, password=password))

    def tearDown(self):
        super(KernelViewsTests, self).tearDown()
        self.client.logout()

    def test__project_propagation(self):
        url_404 = reverse('project-propagate', kwargs={'pk': self.helper_create_uuid()})
        response = self.client.patch(url_404)
        self.assertEqual(response.status_code, 404)

        project = self.helper_create_project()
        url = reverse('project-propagate', kwargs={'pk': project.pk})

        with mock.patch('aether.odk.api.views.propagate_kernel_project',
                        return_value=True) as mock_kernel:
            response = self.client.patch(url)
            self.assertEqual(response.status_code, 200)
            mock_kernel.assert_called_once_with(project=project, family=None)

        with mock.patch('aether.odk.api.views.propagate_kernel_project',
                        side_effect=[KernelPropagationError]) as mock_kernel:
            response = self.client.patch(url, json.dumps({'family': 'testing'}), content_type='application/json')
            self.assertEqual(response.status_code, 400)
            mock_kernel.assert_called_once_with(project=project, family='testing')

    def test__xform_propagation(self):
        url_404 = reverse('xform-propagate', kwargs={'pk': 0})
        response = self.client.patch(url_404)
        self.assertEqual(response.status_code, 404)

        xform = self.helper_create_xform()
        url = reverse('xform-propagate', kwargs={'pk': xform.pk})

        with mock.patch('aether.odk.api.views.propagate_kernel_artefacts',
                        return_value=True) as mock_kernel:
            response = self.client.patch(url)
            self.assertEqual(response.status_code, 200)
            mock_kernel.assert_called_once_with(xform=xform, family=None)

        with mock.patch('aether.odk.api.views.propagate_kernel_artefacts',
                        side_effect=[KernelPropagationError]) as mock_kernel:
            response = self.client.patch(url, json.dumps({'family': 'testing'}), content_type='application/json')
            self.assertEqual(response.status_code, 400)
            mock_kernel.assert_called_once_with(xform=xform, family='testing')
