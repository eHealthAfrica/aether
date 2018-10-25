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

from aether.kernel.api import utils

from . import EXAMPLE_NESTED_SOURCE_DATA


class UtilsTests(TestCase):

    def test_json_prettified_simple(self):
        data = {}
        expected = '<pre><span></span><span class="p">{}</span>\n</pre>'
        pretty = str(utils.json_prettified(data))
        self.assertTrue(expected in pretty, pretty)

    def test_code_prettified_simple(self):
        data = 'print "Hello world!"'
        expected = '<span class="s2">&quot;Hello world!&quot;</span>'

        pretty = str(utils.code_prettified(data))
        self.assertTrue(expected in pretty, pretty)

    def test_json_printable(self):
        data = [{'dob': '2000-01-01', 'name': 'PersonA'}]
        expected = [{'dob': '2000-01-01', 'name': 'PersonA'}]
        printable = utils.json_printable(data)
        self.assertEquals(printable, expected)

    def test_json_printable_other_obj(self):
        data = 2
        expected = 2
        printable = utils.json_printable(data)
        self.assertEquals(printable, expected)

    def test_merge_objects(self):
        source = {'a': 0, 'c': 3}
        target = {'a': 1, 'b': 2}

        self.assertEqual(utils.merge_objects(source, target, 'last_write_wins'),
                         {'a': 1, 'b': 2, 'c': 3})
        self.assertEqual(source,
                         {'a': 1, 'b': 2, 'c': 3},
                         'source content is replaced')

        source = {'a': 0, 'c': 3}
        target = {'a': 1, 'b': 2}
        self.assertEqual(utils.merge_objects(source, target, 'first_write_wins'),
                         {'a': 0, 'b': 2, 'c': 3})
        self.assertEqual(target,
                         {'a': 0, 'b': 2, 'c': 3},
                         'target content is replaced')

    def test_object_contains(self):
        data = EXAMPLE_NESTED_SOURCE_DATA
        source_house = data['data']['houses'][0]
        other_house = data['data']['houses'][1]
        test_person = source_house['people'][0]

        is_included = utils.object_contains(test_person, source_house)
        not_included = utils.object_contains(test_person, other_house)

        self.assertTrue(is_included), 'Person should be found in this house.'
        self.assertFalse(not_included, 'Person should not found in this house.')
