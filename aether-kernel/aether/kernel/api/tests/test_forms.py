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

from django.test import TestCase

from aether.kernel.api import forms


class FormsTest(TestCase):

    def test_str_to_json(self):
        data = '{"dob": "2000-01-01", "name":"PersonA"}'
        expected = {'dob': '2000-01-01', 'name': 'PersonA'}
        result = str(forms.str_to_json(data))
        self.assertTrue(str(expected) in result, result)

    def test_str_to_json_no_data(self):
        data = None
        expected = {}
        result = str(forms.str_to_json(data))
        self.assertTrue(str(expected) in result, result)
