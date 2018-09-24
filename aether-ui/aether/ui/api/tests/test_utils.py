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

import ast

from django.test import TestCase

from .. import utils


class ViewsTest(TestCase):
    project_id = ''

    def test_kernel_data_request(self):
        result = utils.kernel_data_request('projects/')
        self.assertIn('count', result)
        with self.assertRaises(Exception):
            utils.kernel_data_request('projectss', 'post', {'wrong-input': 'tests'})

    def test_convert_entity_types(self):
        with self.assertRaises(Exception) as exc:
            utils.convert_entity_types({'Person': '123456'})
            exception = ast.literal_eval(str(exc.exception))
            self.assertEqual(exception['object_name'], 'unknown')
