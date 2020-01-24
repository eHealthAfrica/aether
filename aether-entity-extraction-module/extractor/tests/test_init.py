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

from extractor import main


class InitTests(TestCase):

    def test_manager_setup(self):
        manager = main()
        self.assertEqual(len(manager.pending_submissions), 0)
        self.assertEqual(len(manager.processed_submissions.keys()), 0)
        self.assertEqual(len(manager.extracted_entities.keys()), 0)
        # without this the redis thread will keep alive forever
        manager.stop()
