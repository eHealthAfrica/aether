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
import os

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from aether.sync.api.kernel_utils import KernelPropagationError
from aether.sync.api.models import Project
from aether.sync.api.tests import DEVICE_TEST_FILE


class MockedScheduler():
    def get_jobs(self):
        return []


def get_scheduler_mocked(*args, **kwargs):
    return MockedScheduler()


class CheckRQCommandTest(TestCase):

    def setUp(self):
        # Redirect to /dev/null in order to not clutter the test log.
        self.out = open(os.devnull, 'w')

    def test__check_rq(self):
        try:
            call_command('check_rq', stdout=self.out, stderr=self.out)
            self.assertTrue(True)
        except Exception:
            self.assertTrue(False)

    @mock.patch('aether.sync.management.commands.check_rq.get_scheduler',
                side_effect=get_scheduler_mocked)
    def test__check_rq__error(self, *args):
        self.assertRaises(
            RuntimeError,
            call_command,
            'check_rq',
            stdout=self.out,
            stderr=self.out,
        )


class PropagateProjectsCommandTest(TestCase):

    def setUp(self):
        # Redirect to /dev/null in order to not clutter the test log.
        self.out = open(os.devnull, 'w')

    @mock.patch('aether.sync.management.commands.propagate_projects.propagate_kernel_project')
    def test__propagate__no_data(self, mock_propagate):
        try:
            call_command('propagate_projects', stdout=self.out, stderr=self.out)
            self.assertTrue(True)
        except Exception:
            self.assertTrue(False)
        mock_propagate.assert_not_called()

    @mock.patch('aether.sync.management.commands.propagate_projects.propagate_kernel_project')
    def test__propagate__success(self, mock_propagate):
        Project.objects.create(name='Test')

        try:
            call_command('propagate_projects', stdout=self.out, stderr=self.out)
            self.assertTrue(True)
        except Exception:
            self.assertTrue(False)
        mock_propagate.assert_called_once()

    @mock.patch('aether.sync.management.commands.propagate_projects.propagate_kernel_project',
                side_effect=KernelPropagationError)
    def test__propagate__error(self, mock_propagate):
        Project.objects.create(name='Test')

        try:
            call_command('propagate_projects', stdout=self.out, stderr=self.out)
            self.assertTrue(True)
        except Exception:
            self.assertTrue(False)
        mock_propagate.assert_called_once()


class LoadFileSyncCommandTest(TestCase):

    def setUp(self):
        # Redirect to /dev/null in order to not clutter the test log.
        self.out = open(os.devnull, 'w')

    def test__filename_argument_is_required(self):
        self.assertRaises(
            CommandError,
            call_command,
            'load_file_sync',
            stdout=self.out,
        )

    @mock.patch('aether.sync.management.commands.load_file_sync.load_backup_file')
    def test__load_file(self, mock_load):
        try:
            call_command('load_file_sync',
                         f'--filename={DEVICE_TEST_FILE}',
                         stdout=self.out,
                         stderr=self.out)
            self.assertTrue(True)
        except Exception:
            self.assertTrue(False)
        mock_load.assert_called_once()


class SetUpCouchDBCommandTest(TestCase):
    def setUp(self):
        # Redirect to /dev/null in order to not clutter the test log.
        self.out = open(os.devnull, 'w')

    @mock.patch('aether.sync.management.commands.setup_couchdb.create_db')
    def test__setup_couchdb(self, mock_create):
        try:
            call_command('setup_couchdb',
                         stdout=self.out,
                         stderr=self.out)
            self.assertTrue(True)
        except Exception:
            self.assertTrue(False)
        mock_create.assert_called()
