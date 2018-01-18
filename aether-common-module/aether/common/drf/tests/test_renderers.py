from django.test import TestCase, RequestFactory

from ..renderers import CustomCSVRenderer

factory = RequestFactory()
EOF = b'\r\n'


class PaginationTests(TestCase):

    def helper__render(self, data, request=None):
        if request is None:
            request = factory.get('/')

        return b''.join(CustomCSVRenderer().render(
            data=data,
            renderer_context={'request': request},
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
