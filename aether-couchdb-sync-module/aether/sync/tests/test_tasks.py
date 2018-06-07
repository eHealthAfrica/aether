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

from django.test import TestCase
from ..tasks import import_synced_devices_task


class ImporterTasksTests(TestCase):

    @mock.patch('aether.sync.tasks.import_synced_devices')
    @mock.patch('aether.sync.tasks.test_connection', return_value=False)
    def test__import_synced_devices_task_without_kernel(self, mock_test, mock_task):
        self.assertEqual(import_synced_devices_task(), {})
        mock_task.assert_not_called()

    @mock.patch('aether.sync.tasks.import_synced_devices')
    @mock.patch('aether.sync.tasks.test_connection', return_value=True)
    def test__import_synced_devices_task_with_kernel(self, mock_test, mock_task):
        self.assertNotEqual(import_synced_devices_task(), {})
        mock_task.assert_called()
