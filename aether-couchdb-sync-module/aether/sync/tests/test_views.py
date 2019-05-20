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

from django.urls import reverse
from django.test import TestCase


class MockedScheduler():
    def get_jobs(self):
        return []


def get_scheduler_mocked(*args, **kwargs):
    return MockedScheduler()


class TestViews(TestCase):

    def test__check_rq(self):
        response = self.client.get(reverse('check-rq'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})

    @mock.patch('aether.sync.views.get_scheduler', side_effect=get_scheduler_mocked)
    def test__check_rq__error(self, *args):
        response = self.client.get(reverse('check-rq'))
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {})
