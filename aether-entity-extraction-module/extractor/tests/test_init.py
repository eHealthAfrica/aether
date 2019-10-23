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

import collections
import requests
from unittest import TestCase
from .. import main, start_web_server


class InitTests(TestCase):

    def test_manager_setup(self):
        container = main()
        self.assertEqual(container.SUBMISSION_QUEUE, collections.deque())
        self.assertEqual(container.PROCESSED_SUBMISSIONS, collections.deque())
        self.assertEqual(container.PROCESSED_ENTITIES, collections.deque())
        container.stop()

    def test_web_server_setup(self):
        ws = start_web_server()
        response = requests.get('http://localhost:5007/exm/healthcheck')
        self.assertTrue(response.json()['healthy'])
        ws.stop()
