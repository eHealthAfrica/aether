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

import copy
import json
import mock

from openpyxl import load_workbook

from django.contrib.auth import get_user_model
from django.db.models import F
from django.http import FileResponse, HttpResponse
from django.test import TestCase
from django.urls import reverse

from .. import models
from ..exporter import (
    __filter_paths as filter_paths,
    __flatten_dict as flatten_dict,
    __generate_workbook as generate,
    __get_label as get_label,
    __parse_row as parse_row,

    XLSX_CONTENT_TYPE,
    CSV_CONTENT_TYPE,
)

from . import EXAMPLE_MAPPING, EXAMPLE_SCHEMA, EXAMPLE_SOURCE_DATA

EXAMPLE_PATHS = [
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

EXAMPLE_LABELS = {
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

EXAMPLE_PAYLOAD = {
    'id': '6b90cfb6-0ee6-4035-94bc-fb7f3e56d790',
    '_id': 'my-test-form',
    'date': '2017-07-14T00:00:00',
    'lang': 'EN,FR',
    'meta': {
        'instanceID': 'uuid:cef69d9d-ebd9-408f-8bc6-9d418bb083d9',
        'instanceName': 'Something_that_is_not_None',
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
            'value': 'One',
        },
        {
            'index': 2,
            'value': 'Two',
        },
        {
            'index': 3,
            'value': 'Three',
        },
    ],
    'number2': 3.56,
    '_version': 'test-1.0',
    'datetime': '2017-07-14T16:38:47.151000+02:00',
    'deviceid': '355217062209730',
    'location': {
        'accuracy': 22,
        'altitude': 108,
        'latitude': 52.52469543,
        'longitude': 13.39282687,
    },
    'option_a': {
        'choice_a': 'A',
    },
    'option_b': None,
    'starttime': '2017-07-14T16:37:08.966000+02:00',
    'iterate_one': [
        {
            'item': 'one',
        },
    ],
    'iterate_none': [],
    'location_none': None,
}


def assign_mapping_entities(mapping, projectschemas):
    entities = {}
    for projectschema in projectschemas:
        entities[projectschema.schema.definition['name']] = str(projectschema.pk)
    mapping_ = copy.deepcopy(mapping)
    mapping_['entities'] = entities
    return mapping_


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


class ExporterViewsTest(TestCase):

    def setUp(self):
        username = 'test'
        email = 'test@example.com'
        password = 'testtest'
        self.user = get_user_model().objects.create_user(username, email, password)
        self.assertTrue(self.client.login(username=username, password=password))

        project = models.Project.objects.create(
            name='project1',
        )
        schema = models.Schema.objects.create(
            name='schema1',
            definition=EXAMPLE_SCHEMA,
        )
        projectschema = models.ProjectSchema.objects.create(
            name='projectschema1',
            project=project,
            schema=schema,
        )
        mapping_definition = assign_mapping_entities(
            mapping=EXAMPLE_MAPPING,
            projectschemas=[projectschema],
        )
        mapping = models.Mapping.objects.create(
            name='mapping1',
            definition=mapping_definition,
            project=project,
        )
        submission = models.Submission.objects.create(
            payload=EXAMPLE_SOURCE_DATA,
            mapping=mapping,
        )
        models.Entity.objects.create(
            payload=EXAMPLE_PAYLOAD,
            projectschema=projectschema,
            submission=submission,
        )

    def tearDown(self):
        self.client.logout()

    def test__generate_workbook(self):
        data = models.Entity.objects.annotate(exporter_data=F('payload'))
        xlsx_path = generate(EXAMPLE_PATHS, EXAMPLE_LABELS, data)
        wb = load_workbook(filename=xlsx_path, read_only=True)
        _id = str(models.Entity.objects.first().pk)

        # check workbook content
        ws = wb['#']    # root content

        # check headers
        self.assertEqual(ws['A1'].value, '@')
        self.assertEqual(ws['B1'].value, '@id')
        self.assertEqual(ws['C1'].value, 'Country')
        self.assertEqual(ws['D1'].value, 'Region')
        self.assertEqual(ws['E1'].value, 'What is your name?')
        self.assertEqual(ws['F1'].value, 'Collect your GPS coordinates / latitude')
        self.assertEqual(ws['G1'].value, 'Collect your GPS coordinates / longitude')
        self.assertEqual(ws['H1'].value, 'Collect your GPS coordinates / altitude')
        self.assertEqual(ws['I1'].value, 'Collect your GPS coordinates / accuracy')
        self.assertEqual(ws['J1'].value, 'Take a picture')
        self.assertEqual(ws['K1'].value, 'How many?')
        self.assertEqual(ws['L1'].value, 'Percentage')
        self.assertEqual(ws['M1'].value, 'When?')
        self.assertEqual(ws['N1'].value, 'At?')
        self.assertEqual(ws['O1'].value, 'Choice (A/B)')
        self.assertEqual(ws['P1'].value, 'Option A / Choice A')
        self.assertEqual(ws['Q1'].value, 'Spoken languages')
        self.assertEqual(ws['R1'].value, 'ID')

        # check rows
        self.assertEqual(ws['A2'].value, 1)
        self.assertEqual(ws['B2'].value, _id)
        self.assertEqual(ws['C2'].value, 'CM')
        self.assertEqual(ws['D2'].value, None)
        self.assertEqual(ws['E2'].value, 'Name')
        self.assertEqual(ws['F2'].value, 52.52469543)
        self.assertEqual(ws['G2'].value, 13.39282687)
        self.assertEqual(ws['H2'].value, 108)
        self.assertEqual(ws['I2'].value, 22)
        self.assertEqual(ws['J2'].value, None)
        self.assertEqual(ws['K2'].value, 3)
        self.assertEqual(ws['L2'].value, 3.56)
        self.assertEqual(ws['M2'].value, '2017-07-14T00:00:00')
        self.assertEqual(ws['N2'].value, '2017-07-14T16:38:47.151000+02:00')
        self.assertEqual(ws['O2'].value, 'a')
        self.assertEqual(ws['P2'].value, 'A')
        self.assertEqual(ws['Q2'].value, 'EN,FR')
        self.assertEqual(ws['R2'].value, '6b90cfb6-0ee6-4035-94bc-fb7f3e56d790')

        ws1 = wb['#1']  # first array content

        # check headers
        self.assertEqual(ws1['A1'].value, '@')
        self.assertEqual(ws1['B1'].value, '@id')
        self.assertEqual(ws1['C1'].value, 'Indicate loop elements / #')
        self.assertEqual(ws1['D1'].value, 'Indicate loop elements / # / Index')
        self.assertEqual(ws1['E1'].value, 'Indicate loop elements / # / Value')

        # check rows
        self.assertEqual(ws1['A2'].value, 1)
        self.assertEqual(ws1['B2'].value, _id)
        self.assertEqual(ws1['C2'].value, 0)
        self.assertEqual(ws1['D2'].value, 1)
        self.assertEqual(ws1['E2'].value, 'One')

        self.assertEqual(ws1['A3'].value, 1)
        self.assertEqual(ws1['B3'].value, _id)
        self.assertEqual(ws1['C3'].value, 1)
        self.assertEqual(ws1['D3'].value, 2)
        self.assertEqual(ws1['E3'].value, 'Two')

        self.assertEqual(ws1['A4'].value, 1)
        self.assertEqual(ws1['B4'].value, _id)
        self.assertEqual(ws1['C4'].value, 2)
        self.assertEqual(ws1['D4'].value, 3)
        self.assertEqual(ws1['E4'].value, 'Three')

        ws2 = wb['#2']  # second array content

        # check headers
        self.assertEqual(ws2['A1'].value, '@')
        self.assertEqual(ws2['B1'].value, '@id')
        self.assertEqual(ws2['C1'].value, 'Indicate one / #')
        self.assertEqual(ws2['D1'].value, 'Indicate one / # / Item')

        # check rows
        self.assertEqual(ws2['A2'].value, 1)
        self.assertEqual(ws2['B2'].value, _id)
        self.assertEqual(ws2['C2'].value, 0)
        self.assertEqual(ws2['D2'].value, 'one')

    # -----------------------------
    # SUBMISSIONS
    # -----------------------------

    def test_submissions_export__endpoints(self):
        self.assertEqual(reverse('submission-xlsx'), '/submissions/xlsx/')
        self.assertEqual(reverse('submission-csv'), '/submissions/csv/')

    @mock.patch(
        'aether.kernel.api.views.exporter.export_data',
        side_effect=OSError('[Errno 2] No such file or directory'),
    )
    def test_submissions_export__error__mocked(self, mock_export):
        response = self.client.get(reverse('submission-xlsx'))
        self.assertEquals(response.status_code, 500)
        data = response.json()['detail']
        self.assertIn('Got an error while creating the file:', data)
        self.assertIn('[Errno 2] No such file or directory', data)
        mock_export.assert_called_once()

    @mock.patch(
        'aether.kernel.api.views.exporter.export_data',
        return_value=HttpResponse('bytes', status=200),
    )
    def test_submissions_export__xlsx__mocked(self, mock_export):
        response = self.client.get(reverse('submission-xlsx'))
        self.assertEquals(response.status_code, 200)
        mock_export.assert_called_once_with(
            data=mock.ANY,
            paths=[],
            headers={},
            format='xlsx',
            filename='export',
            offset=0,
            limit=1,
        )

    @mock.patch(
        'aether.kernel.api.views.exporter.export_data',
        return_value=HttpResponse('bytes', status=200),
    )
    def test_submissions_export__csv__mocked(self, mock_export):
        for __ in range(13):
            models.Submission.objects.create(
                payload=EXAMPLE_SOURCE_DATA,
                mapping=models.Mapping.objects.first(),
            )

        response = self.client.post(reverse('submission-csv'), data=json.dumps({
            'paths': ['_id', '_rev'],
            'headers': {'_id': 'id', '_rev': 'rev'},
            'filename': 'submissions',
            'page': 3,
            'page_size': 5,
        }), content_type='application/json')
        self.assertEquals(response.status_code, 200)
        mock_export.assert_called_once_with(
            data=mock.ANY,
            paths=['_id', '_rev'],
            headers={'_id': 'id', '_rev': 'rev'},
            format='csv',
            separator=',',
            filename='submissions',
            offset=10,
            limit=14,  # there was already one submission
        )

    # -----------------------------
    # ENTITIES
    # -----------------------------

    def test_entities_export__endpoints(self):
        self.assertEqual(reverse('entity-xlsx'), '/entities/xlsx/')
        self.assertEqual(reverse('entity-csv'), '/entities/csv/')

    @mock.patch(
        'aether.kernel.api.views.exporter.export_data',
        side_effect=OSError('[Errno 2] No such file or directory'),
    )
    def test_entities_export___error__mocked(self, mock_export):
        response = self.client.get(reverse('entity-csv'))
        self.assertEquals(response.status_code, 500)
        data = response.json()['detail']
        self.assertIn('Got an error while creating the file:', data)
        self.assertIn('[Errno 2] No such file or directory', data)
        mock_export.assert_called_once()

    @mock.patch(
        'aether.kernel.api.views.exporter.export_data',
        return_value=HttpResponse('data', status=200),
    )
    def test_entities_export__xlsx__mocked(self, mock_export):
        response = self.client.get(reverse('entity-xlsx'))
        self.assertEquals(response.status_code, 200)
        mock_export.assert_called_once_with(
            data=mock.ANY,
            paths=['id', '_rev', 'name', 'dob', 'villageID'],
            headers={'id': 'ID', '_rev': 'REVISION', 'name': 'NAME', 'villageID': 'VILLAGE'},
            format='xlsx',
            filename='export',
            offset=0,
            limit=1,
        )

    def test_entities_export__xlsx__empty(self):
        models.Entity.objects.all().delete()
        response = self.client.post(reverse('entity-xlsx'))
        self.assertTrue(response.status_code, 204)

    def test_entities_export__xlsx(self):
        response = self.client.get(reverse('entity-xlsx'))
        self.assertEquals(response.status_code, 200)
        self.assertTrue(isinstance(response, FileResponse))
        self.assertEqual(response['Content-Type'], XLSX_CONTENT_TYPE)

    @mock.patch(
        'aether.kernel.api.views.exporter.export_data',
        return_value=HttpResponse('data', status=200),
    )
    def test_entities_export__csv__mocked(self, mock_export):
        response = self.client.post(reverse('entity-csv'))
        self.assertEquals(response.status_code, 200)
        mock_export.assert_called_once_with(
            data=mock.ANY,
            paths=['id', '_rev', 'name', 'dob', 'villageID'],
            headers={'id': 'ID', '_rev': 'REVISION', 'name': 'NAME', 'villageID': 'VILLAGE'},
            format='csv',
            separator=',',
            filename='export',
            offset=0,
            limit=1,
        )

    def test_entities_export__csv__empty(self):
        models.Entity.objects.all().delete()
        response = self.client.post(reverse('entity-csv'))
        self.assertTrue(response.status_code, 204)

    def test_entities_export__csv(self):
        response = self.client.post(reverse('entity-csv'))
        self.assertEquals(response.status_code, 200)
        self.assertTrue(isinstance(response, FileResponse))
        self.assertEqual(response['Content-Type'], CSV_CONTENT_TYPE)
