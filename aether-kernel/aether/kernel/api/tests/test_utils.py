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

from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from aether.kernel.api import utils, models

from . import (
    EXAMPLE_NESTED_SOURCE_DATA,
    SAMPLE_LOCATION_SCHEMA_DEFINITION,
    SAMPLE_HOUSEHOLD_SCHEMA_DEFINITION,
    EXAMPLE_FIELD_MAPPINGS,
    EXAMPLE_SCHEMA,
    EXAMPLE_SOURCE_DATA_WITH_LOCATION,
    EXAMPLE_FIELD_MAPPINGS_LOCATION
)


@override_settings(MULTITENANCY=False)
class UtilsTests(TestCase):
    def setUp(self):
        username = 'test'
        email = 'test@example.com'
        password = 'testtest'
        self.user = get_user_model().objects.create_user(username, email, password)
        self.assertTrue(self.client.login(username=username, password=password))

        self.project = models.Project.objects.create(
            revision='rev 1',
            name='a project name',
        )

        url = reverse('project-artefacts', kwargs={'pk': self.project.pk})

        data = {
            'mappingsets': [{
                'name': 'Test Mappingset',
                'input': EXAMPLE_SOURCE_DATA_WITH_LOCATION,
                'schema': {},
            }],
            'schemas': [
                {
                    'name': 'Location',
                    'definition': SAMPLE_LOCATION_SCHEMA_DEFINITION,
                },
                {
                    'name': 'Household',
                    'definition': SAMPLE_HOUSEHOLD_SCHEMA_DEFINITION,
                },
                {
                    'name': 'Person',
                    'definition': EXAMPLE_SCHEMA,
                }
            ],
            'mappings': [
                {
                    'name': 'mapping-1',
                    'definition': {
                        'mapping': EXAMPLE_FIELD_MAPPINGS,
                    },
                    'is_active': True,
                    'is_ready_only': False,
                },
                {
                    'name': 'mapping-2',
                    'definition': {
                        'mapping': EXAMPLE_FIELD_MAPPINGS_LOCATION,
                    },
                    'is_active': True,
                    'is_ready_only': False,
                }
            ],
        }
        self.project_artefacts = self.client.patch(
            url,
            data=data,
            content_type='application/json',
        ).json()

    def tearDown(self):
        self.project.delete()
        self.client.logout()

    def test_merge_objects(self):
        source = {'a': 0, 'c': 3}
        target = {'a': 1, 'b': 2}
        self.assertEqual(utils.merge_objects(source, target, 'overwrite'),
                         {'a': 1, 'b': 2})
        self.assertEqual(source,
                         {'a': 0, 'c': 3},
                         'source content is not touched')
        self.assertEqual(target,
                         {'a': 1, 'b': 2},
                         'target content is not touched')

        source = {'a': 0, 'c': 3}
        target = {'a': 1, 'b': 2}
        self.assertEqual(utils.merge_objects(source, target, 'last_write_wins'),
                         {'a': 1, 'b': 2, 'c': 3})
        self.assertEqual(source,
                         {'a': 1, 'b': 2, 'c': 3},
                         'source content is replaced')
        self.assertEqual(target,
                         {'a': 1, 'b': 2},
                         'target content is not touched')

        source = {'a': 0, 'c': 3}
        target = {'a': 1, 'b': 2}
        self.assertEqual(utils.merge_objects(source, target, 'first_write_wins'),
                         {'a': 0, 'b': 2, 'c': 3})
        self.assertEqual(source,
                         {'a': 0, 'c': 3},
                         'source content is not touched')
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

    def test_get_unique_schemas_used(self):
        url = reverse('mapping-detail', kwargs={'pk': self.project_artefacts['mappings'][0]})
        mapping = self.client.get(url).json()
        if mapping['name'] == 'mapping-1':
            mapping_1 = mapping
        else:
            mapping_2 = mapping

        url = reverse('mapping-detail', kwargs={'pk': self.project_artefacts['mappings'][1]})
        mapping = self.client.get(url).json()
        if mapping['name'] == 'mapping-2':
            mapping_2 = mapping
        else:
            mapping_1 = mapping

        self.assertEqual(mapping_2['name'], 'mapping-2')
        self.assertEqual(mapping_1['name'], 'mapping-1')

        result = utils.get_unique_schemas_used([mapping_1['id']])
        self.assertEqual(len(result), 1)
        self.assertEqual(next(iter(result)), 'Person')
        self.assertFalse(result[next(iter(result))]['is_unique'])

        result = utils.get_unique_schemas_used([mapping_2['id']])
        self.assertEqual(len(result), 2)
        self.assertFalse(result['Person']['is_unique'])
        self.assertTrue(result['Location']['is_unique'])

        result = utils.get_unique_schemas_used([mapping_2['id'], mapping_1['id']])
        self.assertEqual(len(result), 2)
        self.assertTrue(result['Person']['is_unique'])
        self.assertTrue(result['Location']['is_unique'])
