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
import os

from django.core.management import call_command
from django.test import TestCase


class MockedScheduler():
    def get_jobs(self):
        return []


def get_scheduler_mocked(*args, **kwargs):
    return MockedScheduler()


class TestSetupAdminCommand(TestCase):

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
