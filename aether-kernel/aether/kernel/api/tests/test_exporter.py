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

from openpyxl import load_workbook

from django.http import FileResponse
from django.test import TestCase

from ..exporter import (
    __filter_paths as filter_paths,
    __flatten_dict as flatten_dict,
    __generate_workbook as generate,
    __get_label as get_label,
    __parse_row as parse_row,

    export_data,
    XLSX_CONTENT_TYPE,
    CSV_CONTENT_TYPE,
)

SAMPLE_PATHS = [
    '_id',
    '_version',
    'starttime',
    'endtime',
    'deviceid',
    'country',
    'region',
    'name',
    'location',
    'location.latitude',
    'location.longitude',
    'location.altitude',
    'location.accuracy',
    'location_none',
    'location_none.latitude',
    'location_none.longitude',
    'location_none.altitude',
    'location_none.accuracy',
    'image',
    'number',
    'number2',
    'date',
    'datetime',
    'option',
    'option_a',
    'option_a.choice_a',
    'option_b',
    'option_b.choice_b',
    'lang',
    'iterate',
    'iterate.#',
    'iterate.#.index',
    'iterate.#.value',
    'iterate_one',
    'iterate_one.#',
    'iterate_one.#.item',
    'iterate_none',
    'iterate_none.#',
    'iterate_none.#.nothing',
    'meta',
    'meta.instanceID',
    'meta.instanceName',
    'id',
]

SAMPLE_LABELS = {
    '_id': 'xForm ID',
    '_version': 'xForm version',
    'country': 'Country',
    'region': 'Region',
    'name': 'What is your name?',
    'location': 'Collect your GPS coordinates',
    'location.latitude': 'latitude',
    'location.longitude': 'longitude',
    'location.altitude': 'altitude',
    'location.accuracy': 'accuracy',
    'location_none': 'Ignore your GPS coordinates',
    'location_none.latitude': 'latitude',
    'location_none.longitude': 'longitude',
    'location_none.altitude': 'altitude',
    'location_none.accuracy': 'accuracy',
    'image': 'Take a picture',
    'number': 'How many?',
    'number2': 'Percentage',
    'date': 'When?',
    'datetime': 'At?',
    'option': 'Choice (A/B)',
    'option_a': 'Option A',
    'option_a.choice_a': 'Choice A',
    'option_b': 'Option B',
    'option_b.choice_b': 'Choice B',
    'lang': 'Spoken languages',
    'iterate': 'Indicate loop elements',
    'iterate.#.index': 'Index',
    'iterate.#.value': 'Value',
    'iterate_one': 'Indicate one',
    'iterate_one.#.item': 'Item',
    'iterate_none': 'Indicate none',
    'iterate_none.#.nothing': 'None',
    'id': 'ID',
}

SAMPLE_ROW = {
    '__id': '1309afad-f55b-43fc-900e-4215ba782ee8',
    '__data': {
        'id': '6b90cfb6-0ee6-4035-94bc-fb7f3e56d790',
        '_id': 'my-test-form',
        'date': '2017-07-14T00:00:00',
        'lang': 'EN,FR',
        'meta': {
            'instanceID': 'uuid:cef69d9d-ebd9-408f-8bc6-9d418bb083d9',
            'instanceName': 'Something_that_is_not_None'
        },
        'name': 'Name',
        'image': None,
        'number': 3,
        'option': 'a',
        'region': None,
        'country': 'CM',
        'endtime': '2017-07-14T16:38:47.151000+02:00',
        'iterate': [
            {
                'index': 1,
                'value': 'One'
            },
            {
                'index': 2,
                'value': 'Two'
            },
            {
                'index': 3,
                'value': 'Three'
            }
        ],
        'number2': 3.56,
        '_version': 'test-1.0',
        'datetime': '2017-07-14T16:38:47.151000+02:00',
        'deviceid': '355217062209730',
        'location': {
            'accuracy': 22,
            'altitude': 108,
            'latitude': 52.52469543,
            'longitude': 13.39282687
        },
        'option_a': {
            'choice_a': 'A'
        },
        'option_b': None,
        'starttime': '2017-07-14T16:37:08.966000+02:00',
        'iterate_one': [
            {
                'item': 'one'
            }
        ],
        'iterate_none': [],
        'location_none': None
    }
}


class ExporterTest(TestCase):

    def test__flatten_dict(self):
        item = {
            'a': {
                'b': 1,
                'z': 'z',
            },
            'c': {
                'd': [{'f': 2}],
            },
        }
        expected = {
            'a.b': 1,
            'a.z': 'z',
            'c.d': [{'f': 2}],
        }

        self.assertEqual(flatten_dict({}), {})
        self.assertEqual(flatten_dict(item), expected)
        self.assertEqual(flatten_dict(flatten_dict(item)), expected)

    def test__filter_paths(self):
        paths = [
            'a',
            'a.b',
            'a.b.*',
            'a.b.*.#',
            'a.b.*.#.x',
            'a.c',
            'a.c.#',
            'a.c.#.y',
            'a.d',
            'a.d.?',
            'a.d.?.e',
            'a.f',
            'a.f.g',
            'z',
        ]
        expected = [
            'a.b',
            'a.c',
            'a.d',
            'a.f.g',
            'z',
        ]

        self.assertEqual(filter_paths(paths), expected)
        self.assertEqual(filter_paths(filter_paths(paths)), expected)

    def test__parse_row(self):
        row = {
            'a': {
                'b': 1,
                'z': 'z',
            },
            'c': {
                'd': [{'f': 2}],
            },
        }

        self.assertEqual(parse_row(row, ['z']), {})
        self.assertEqual(parse_row(row, []), {'a.b': 1, 'a.z': 'z', 'c.d': [{'f': 2}]})

        self.assertEqual(parse_row(row, ['a']), {'a.b': 1, 'a.z': 'z'})
        self.assertEqual(parse_row(row, ['a.b']), {'a.b': 1})
        self.assertEqual(parse_row(row, ['a', 'b', 'a.g']), {'a.b': 1, 'a.z': 'z'})

        self.assertEqual(parse_row(row, ['c']), {'c.d': [{'f': 2}]})

    def test__get_label(self):
        labels = {
            'a': 'Root',
            'a.d.#.e': 'The indexed E',
            'a.*.c': 'The Big C',
            'a.*.c.?.u': 'Join',
            'x.y.?.z': 'Union'
        }

        # should find simple nested properties
        self.assertEqual(get_label('a.b'), 'A / B')
        self.assertEqual(get_label('a', labels), 'Root')
        self.assertEqual(get_label('@.a', labels), 'Root')

        # should detect array properties
        self.assertEqual(get_label('a.d.#.e', labels), 'Root / D / # / The indexed E')

        # should detect map properties
        self.assertEqual(get_label('a.x.c', labels), 'Root / X / The Big C')
        self.assertEqual(get_label('a.x_x.c', labels), 'Root / X x / The Big C')
        self.assertEqual(get_label('a.x__1_x.c', labels), 'Root / X 1 x / The Big C')
        self.assertEqual(get_label('a.x__1._x.c', labels), 'Root / X 1 / X / C')

        self.assertEqual(get_label('a.x.c.z', labels), 'Root / X / The Big C / Z')
        self.assertEqual(get_label('a.x_x.c.z', labels), 'Root / X x / The Big C / Z')
        self.assertEqual(get_label('a.x__1_x.c.z', labels), 'Root / X 1 x / The Big C / Z')

        # should detect union properties
        self.assertEqual(get_label('a.x.c.u', labels), 'Root / X / The Big C / Join')
        self.assertEqual(get_label('a.x_x.c.u', labels), 'Root / X x / The Big C / Join')
        self.assertEqual(get_label('a.x__1_x.c.u', labels), 'Root / X 1 x / The Big C / Join')
        self.assertEqual(get_label('a.x__1._x.c.u', labels), 'Root / X 1 / X / C / U')

        self.assertEqual(get_label('x.y.z', labels), 'X / Y / Union')
        self.assertEqual(get_label('x.y.a.z', labels), 'X / Y / A / Z')

    def test__generate_workbook(self):
        paths = filter_paths(SAMPLE_PATHS)
        xlsx_path = generate(paths, SAMPLE_LABELS, [SAMPLE_ROW])
        wb = load_workbook(filename=xlsx_path)
        _id = SAMPLE_ROW['__id']

        # check workbook content
        ws = wb['#']    # root content

        # check headers
        self.assertEqual(ws['A1'].value, '@id')
        self.assertEqual(ws['B1'].value, 'Country')
        self.assertEqual(ws['C1'].value, 'Region')
        self.assertEqual(ws['D1'].value, 'What is your name?')
        self.assertEqual(ws['E1'].value, 'Collect your GPS coordinates / latitude')
        self.assertEqual(ws['F1'].value, 'Collect your GPS coordinates / longitude')
        self.assertEqual(ws['G1'].value, 'Collect your GPS coordinates / altitude')
        self.assertEqual(ws['H1'].value, 'Collect your GPS coordinates / accuracy')
        self.assertEqual(ws['I1'].value, 'Take a picture')
        self.assertEqual(ws['J1'].value, 'How many?')
        self.assertEqual(ws['K1'].value, 'Percentage')
        self.assertEqual(ws['L1'].value, 'When?')
        self.assertEqual(ws['M1'].value, 'At?')
        self.assertEqual(ws['N1'].value, 'Choice (A/B)')
        self.assertEqual(ws['O1'].value, 'Option A / Choice A')
        self.assertEqual(ws['P1'].value, 'Spoken languages')
        self.assertEqual(ws['Q1'].value, 'ID')

        # check rows
        self.assertEqual(ws['A2'].value, _id)
        self.assertEqual(ws['B2'].value, 'CM')
        self.assertEqual(ws['C2'].value, None)
        self.assertEqual(ws['D2'].value, 'Name')
        self.assertEqual(ws['E2'].value, 52.52469543)
        self.assertEqual(ws['F2'].value, 13.39282687)
        self.assertEqual(ws['G2'].value, 108)
        self.assertEqual(ws['H2'].value, 22)
        self.assertEqual(ws['I2'].value, None)
        self.assertEqual(ws['J2'].value, 3)
        self.assertEqual(ws['K2'].value, 3.56)
        self.assertEqual(ws['L2'].value, '2017-07-14T00:00:00')
        self.assertEqual(ws['M2'].value, '2017-07-14T16:38:47.151000+02:00')
        self.assertEqual(ws['N2'].value, 'a')
        self.assertEqual(ws['O2'].value, 'A')
        self.assertEqual(ws['P2'].value, 'EN,FR')
        self.assertEqual(ws['Q2'].value, '6b90cfb6-0ee6-4035-94bc-fb7f3e56d790')

        ws1 = wb['#1']  # first array content

        # check headers
        self.assertEqual(ws1['A1'].value, '@id')
        self.assertEqual(ws1['B1'].value, 'Indicate loop elements / #')
        self.assertEqual(ws1['C1'].value, 'Indicate loop elements / # / Index')
        self.assertEqual(ws1['D1'].value, 'Indicate loop elements / # / Value')

        # check rows
        self.assertEqual(ws1['A2'].value, _id)
        self.assertEqual(ws1['B2'].value, 0)
        self.assertEqual(ws1['C2'].value, 1)
        self.assertEqual(ws1['D2'].value, 'One')

        self.assertEqual(ws1['A3'].value, _id)
        self.assertEqual(ws1['B3'].value, 1)
        self.assertEqual(ws1['C3'].value, 2)
        self.assertEqual(ws1['D3'].value, 'Two')

        self.assertEqual(ws1['A4'].value, _id)
        self.assertEqual(ws1['B4'].value, 2)
        self.assertEqual(ws1['C4'].value, 3)
        self.assertEqual(ws1['D4'].value, 'Three')

        ws2 = wb['#2']  # second array content

        # check headers
        self.assertEqual(ws2['A1'].value, '@id')
        self.assertEqual(ws2['B1'].value, 'Indicate one / #')
        self.assertEqual(ws2['C1'].value, 'Indicate one / # / Item')

        # check rows
        self.assertEqual(ws2['A2'].value, _id)
        self.assertEqual(ws2['B2'].value, 0)
        self.assertEqual(ws2['C2'].value, 'one')

    def test__export_data(self):
        response = export_data([SAMPLE_ROW], SAMPLE_PATHS, SAMPLE_LABELS)
        self.assertTrue(isinstance(response, FileResponse))
        self.assertEqual(response['Content-Type'], XLSX_CONTENT_TYPE)

    def test__export_data__csv(self):
        response = export_data([SAMPLE_ROW], SAMPLE_PATHS, SAMPLE_LABELS, format='csv')
        self.assertTrue(isinstance(response, FileResponse))
        self.assertEqual(response['Content-Type'], CSV_CONTENT_TYPE)
