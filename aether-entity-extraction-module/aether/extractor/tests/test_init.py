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

from unittest import TestCase

from aether.extractor import main


class InitTests(TestCase):

    def setUp(self):
        super(InitTests, self).setUp()
        self.container = main()

    def test_manager_setup(self):
        self.assertFalse(self.container.stopped)
        self.assertTrue(self.container.is_alive())
        self.assertEqual(self.container.processed_submissions.qsize(), 0)

        # try to start again
        with self.assertRaises(RuntimeError):
            self.container.start()

    def tearDown(self):
        self.container.stop()
        self.assertTrue(self.container.stopped)
        self.assertFalse(self.container.is_alive())

        # try to start again
        with self.assertRaises(RuntimeError):
            self.container.stop()

        super(InitTests, self).tearDown()
