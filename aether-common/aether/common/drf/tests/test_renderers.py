from django.test import TestCase

from ..renderers import CustomCSVRenderer


class PaginationTests(TestCase):

    def setUp(self):
        self.renderer = CustomCSVRenderer()

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
            self.renderer.render(data),
            b'a\r\n1\r\n2\r\n3\r\n4\r\n'
        )

    def test_without_pagination(self):
        data = [
            {'a': 1},
            {'a': 2},
            {'a': 3},
            {'a': 4},
        ]

        self.assertEqual(
            self.renderer.render(data),
            b'a\r\n1\r\n2\r\n3\r\n4\r\n'
        )

    def test_simple_json(self):
        data = [
            {'a': 1, 'b': 1},
            {'a': 2, 'b': 2},
            {'a': 3, 'c': 3},
            {'a': 4, 'd': 4},
        ]

        self.assertEqual(
            self.renderer.render(data),
            b'a,b,c,d\r\n1,1,,\r\n2,2,,\r\n3,,3,\r\n4,,,4\r\n',
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
            self.renderer.render(data),
            b'a,b,b.c,c,d\r\n1,,1,,\r\n2,2,,,\r\n3,,,3,\r\n4,,,,4\r\n',
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
            self.renderer.render(data),
            b'a,b.0,b.1,b.2\r\n1,3,,\r\n2,4,5,\r\n3,6,,\r\n4,7,8,9\r\n',
            'analyzes the array length'
        )
