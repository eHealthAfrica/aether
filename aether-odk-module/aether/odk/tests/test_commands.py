# Copyright (C) 2023 by eHealth Africa : http://www.eHealthAfrica.org
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
import os

from django.core.management import call_command
from django.test import TestCase

from aether.odk.api.kernel_utils import KernelPropagationError
from aether.odk.api.models import Project


class PropagateProjectsCommandTest(TestCase):

    def setUp(self):
        # Redirect to /dev/null in order to not clutter the test log.
        self.out = open(os.devnull, 'w')

    @mock.patch('aether.odk.management.commands.propagate_projects.propagate_kernel_project')
    def test__propagate__no_data(self, mock_propagate):
        try:
            call_command('propagate_projects', stdout=self.out, stderr=self.out)
            self.assertTrue(True)
        except Exception:
            self.assertTrue(False)
        mock_propagate.assert_not_called()

    @mock.patch('aether.odk.management.commands.propagate_projects.propagate_kernel_project')
    def test__propagate__success(self, mock_propagate):
        Project.objects.create(name='Test')

        try:
            call_command('propagate_projects', stdout=self.out, stderr=self.out)
            self.assertTrue(True)
        except Exception:
            self.assertTrue(False)
        mock_propagate.assert_called_once()

    @mock.patch('aether.odk.management.commands.propagate_projects.propagate_kernel_project',
                side_effect=KernelPropagationError)
    def test__propagate__error(self, mock_propagate):
        Project.objects.create(name='Test')

        try:
            call_command('propagate_projects', stdout=self.out, stderr=self.out)
            self.assertTrue(True)
        except Exception:
            self.assertTrue(False)
        mock_propagate.assert_called_once()
