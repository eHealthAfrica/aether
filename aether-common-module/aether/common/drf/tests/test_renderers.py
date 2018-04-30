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
# software distributed under the License is distributed on anx
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from django.test import TestCase, RequestFactory
from rest_framework.request import Request

from ..renderers import CustomCSVRenderer, apply_label_rules

factory = RequestFactory()
EOF = b'\r\n'


class CustomCSVRendererTests(TestCase):

    def helper__render(self, data, request=None):
        if request is None:
            request = factory.get('/')

        return b''.join(CustomCSVRenderer().render(
            data=data,
            renderer_context={'request': Request(request)},
        ))

    def test_with_no_data(self):
        self.assertEqual(
            self.helper__render(None),
            b''
        )

    def test_with_paginated_results(self):
        data = {
            'results': [
                {'a': 1},
                {'a': 2},
                {'a': 3},
                {'a': 4},
            ],
            'previous': None,
            'next': 'http://testserver/?page=2',
            'count': 1000,
        }

        self.assertEqual(
            self.helper__render(data),
            b''.join([
                b'a', EOF,
                b'1', EOF,
                b'2', EOF,
                b'3', EOF,
                b'4', EOF,
            ])
        )

    def test_without_pagination(self):
        data = [
            {'a': 1},
            {'a': 2},
            {'a': 3},
            {'a': 4},
        ]

        self.assertEqual(
            self.helper__render(data),
            b''.join([
                b'a', EOF,
                b'1', EOF,
                b'2', EOF,
                b'3', EOF,
                b'4', EOF,
            ])
        )

    def test_simple_json(self):
        data = [
            {'a': 1, 'b': 1},
            {'a': 2, 'b': 2},
            {'a': 3, 'c': 3},
            {'a': 4, 'd': 4},
        ]

        self.assertEqual(
            self.helper__render(data),
            b''.join([
                b'a,b,c,d', EOF,
                b'1,1,,', EOF,
                b'2,2,,', EOF,
                b'3,,3,', EOF,
                b'4,,,4', EOF,
            ]),
            'analyzes ALL results schema'
        )

    def test_simple_json_nested(self):
        data = [
            {'a': 1, 'b': {'c': 1}},
            {'a': 2, 'b': 2},
            {'a': 3, 'c': 3},
            {'a': 4, 'd': 4},
        ]

        self.assertEqual(
            self.helper__render(data),
            b''.join([
                b'a,b,b.c,c,d', EOF,
                b'1,,1,,', EOF,
                b'2,2,,,', EOF,
                b'3,,,3,', EOF,
                b'4,,,,4', EOF,
            ]),
            'analyzes ALL results schema even with nested/repeated properties'
        )

    def test_json_with_arrays(self):
        data = [
            {'a': 1, 'b': [3]},
            {'a': 2, 'b': [4, 5]},
            {'a': 3, 'b': [6]},
            {'a': 4, 'b': [7, 8, 9]},
        ]

        self.assertEqual(
            self.helper__render(data),
            b''.join([
                b'a,b.0,b.1,b.2', EOF,
                b'1,3,,', EOF,
                b'2,4,5,', EOF,
                b'3,6,,', EOF,
                b'4,7,8,9', EOF,
            ]),
            'analyzes the array length'
        )

    def test_json_with_csv_headers(self):
        data = [
            {'a': 1, 'b': [3],       'c': {'d': {'e': 1}}},
            {'a': 2, 'b': [4, 5],    'c': {'d': {'f': 2}}},
            {'a': 3, 'b': [6],       'c': {'g': {'h': 3}}},
            {'a': 4, 'b': [7, 8, 9], 'c': {'g': {'i': 4}}},
        ]
        request = factory.get('/', {'columns': 'a,b.0,b.1,c.d'})

        self.assertEqual(
            self.helper__render(data, request),
            b''.join([
                b'a,b.0,b.1,c.d.e,c.d.f', EOF,
                b'1,3,,1,', EOF,
                b'2,4,5,,2', EOF,
                b'3,6,,,', EOF,
                b'4,7,8,,', EOF,
            ]),
            'filters columns with the csv header'
        )

    def test_json_with_csv_labels(self):
        data = [
            {'a': 1, 'b': [3]},
            {'a': 2, 'b': [4, 5]},
            {'a': 3, 'b': [6]},
            {'a': 4, 'b': [7, 8, 9]},
        ]
        request = factory.get('/', {
            'parse_columns': 'split#.,title',
            'rule_sep': '#',
        })

        self.assertEqual(
            self.helper__render(data, request),
            b''.join([
                b'A,B 0,B 1,B 2', EOF,
                b'1,3,,', EOF,
                b'2,4,5,', EOF,
                b'3,6,,', EOF,
                b'4,7,8,9', EOF,
            ]),
            'parse header labels'
        )

    def test_json_with_csv_headers_and_labels(self):
        data = [
            {'a': 1, 'b': [3],       'c': {'d': {'e': 1}}},
            {'a': 2, 'b': [4, 5],    'c': {'d': {'f': 2}}},
            {'a': 3, 'b': [6],       'c': {'g': {'h': 3}}},
            {'a': 4, 'b': [7, 8, 9], 'c': {'g': {'i': 4}}},
        ]
        request = factory.get('/', {
            'columns': 'a|b.0|b.1|c.d',
            'parse_columns': 'split:.|title',
            'columns_sep': '|',
        })

        self.assertEqual(
            self.helper__render(data, request),
            b''.join([
                b'A,B 0,B 1,C D E,C D F', EOF,
                b'1,3,,1,', EOF,
                b'2,4,5,,2', EOF,
                b'3,6,,,', EOF,
                b'4,7,8,,', EOF,
            ]),
            'filters columns with the csv header and parse header labels'
        )

    def test_rules__unknown(self):
        self.assertEqual(apply_label_rules(['something'], 'a'), 'a')

    def test_rules__remove_prefix(self):
        self.assertEqual(apply_label_rules(['remove-prefix:a.'], 'a.b'), 'b')
        self.assertEqual(apply_label_rules(['remove-prefix:b.'], 'a.b'), 'a.b')
        self.assertEqual(apply_label_rules(['remove-prefix:'], 'a.b'), 'a.b')

    def test_rules__remove_suffix(self):
        self.assertEqual(apply_label_rules(['remove-suffix:.a'], 'a.b'), 'a.b')
        self.assertEqual(apply_label_rules(['remove-suffix:.b'], 'a.b'), 'a')
        self.assertEqual(apply_label_rules(['remove-suffix:'], 'a.b'), 'a.b')

    def test_rules__text_case(self):
        self.assertEqual(apply_label_rules(['lower'], 'AeIoU'), 'aeiou')
        self.assertEqual(apply_label_rules(['upper'], 'AeIoU'), 'AEIOU')
        self.assertEqual(apply_label_rules(['title'], 'AeIoU bcD'), 'Aeiou Bcd')
        self.assertEqual(apply_label_rules(['capitalize'], 'AeIoU bcD'), 'Aeiou bcd')

    def test_rules__replace(self):
        self.assertEqual(apply_label_rules(['replace:.:_'], 'a.e.i.o.u'), 'a_e_i_o_u')
        self.assertEqual(apply_label_rules(['replace$.$: $'], 'a.b.c.d', '$'), 'a: b: c: d')

        # error in rule -> do nothing
        self.assertEqual(apply_label_rules(['replace:'], 'a.e.i.o.u'), 'a.e.i.o.u')
        self.assertEqual(apply_label_rules(['replace:.'], 'a.e.i.o.u'), 'a.e.i.o.u')

        # edge cases
        self.assertEqual(apply_label_rules(['replace:.:'], 'a.b.c.d'), 'abcd')
        self.assertEqual(apply_label_rules(['replace::'], 'a.b.c.d'), 'a.b.c.d')
        self.assertEqual(apply_label_rules(['replace::-'], 'abcd'), '-a-b-c-d-')

    def test_rules__split(self):
        self.assertEqual(apply_label_rules(['split:.'], 'a.e.i.o.u'), 'a e i o u')
        self.assertEqual(apply_label_rules(['replace:.: '], 'a.e.i.o.u'), 'a e i o u')

    def test_rules__chained(self):
        self.assertEqual(
            apply_label_rules([
                'remove-prefix:a.',
                'remove-suffix:.z',
                'whatever',  # unknown rule, ignore it
                'split:.',
                'split:_',
                'title',
            ], 'a.my.properTy_NaMe.z'),
            'My Property Name'
        )

        self.assertEqual(
            apply_label_rules([
                'remove-prefix:a.',
                'remove-suffix:.z',
                'replace:.',  # wrong rule in between (undo changes)
                'split:_',
                'title',
            ], 'a.my.properTy_NaMe.z'),
            'a.my.properTy_NaMe.z'
        )
