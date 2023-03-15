# Copyright (C) 2023 by eHealth Africa : http://www.eHealthAfrica.org
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

import uuid
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from aether.kernel.api import utils, models

from . import (
    SAMPLE_LOCATION_SCHEMA_DEFINITION,
    SAMPLE_HOUSEHOLD_SCHEMA_DEFINITION,
    EXAMPLE_FIELD_MAPPINGS,
    EXAMPLE_SCHEMA,
    EXAMPLE_SOURCE_DATA_WITH_LOCATION,
    EXAMPLE_FIELD_MAPPINGS_LOCATION
)


@override_settings(MULTITENANCY=False)
class UtilsTests(TestCase):
    mapping = None

    def setUp(self):
        username = 'test'
        email = 'test@example.com'
        password = 'testtest'
        get_user_model().objects.create_user(username, email, password)
        self.assertTrue(self.client.login(username=username, password=password))

        self.project = models.Project.objects.create(
            revision='rev 1',
            name='a project name',
        )

        self.mappingset_id = str(uuid.uuid4())
        self.mapping_1 = str(uuid.uuid4())
        self.mapping_2 = str(uuid.uuid4())

        artefacts = {
            'mappingsets': [{
                'id': self.mappingset_id,
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
                },
            ],
            'mappings': [
                {
                    'id': self.mapping_1,
                    'name': 'mapping-1',
                    'definition': {
                        'mapping': EXAMPLE_FIELD_MAPPINGS,
                    },
                    'is_active': True,
                    'is_ready_only': False,
                    'mappingset': self.mappingset_id,
                },
                {
                    'id': self.mapping_2,
                    'name': 'mapping-2',
                    'definition': {
                        'mapping': EXAMPLE_FIELD_MAPPINGS_LOCATION,
                    },
                    'is_active': True,
                    'is_ready_only': False,
                    'mappingset': self.mappingset_id,
                },
            ],
        }
        self.client.patch(
            reverse('project-artefacts', kwargs={'pk': self.project.pk}),
            data=artefacts,
            content_type='application/json',
        )

    def tearDown(self):
        self.project.delete()
        self.client.logout()

    def test_get_unique_schemas_used(self):
        result = utils.get_unique_schemas_used([self.mapping_1])
        self.assertEqual(len(result), 1)
        self.assertEqual(next(iter(result)), 'Person')
        self.assertFalse(result[next(iter(result))]['is_unique'])

        result = utils.get_unique_schemas_used([self.mapping_2])
        self.assertEqual(len(result), 2)
        self.assertFalse(result['Person']['is_unique'])
        self.assertTrue(result['Location']['is_unique'])

        result = utils.get_unique_schemas_used([self.mapping_1, self.mapping_2])
        self.assertEqual(len(result), 2)
        self.assertTrue(result['Person']['is_unique'])
        self.assertTrue(result['Location']['is_unique'])

    def test_bulk_delete_by_mappings_mapping(self):
        opts = {
            'entities': True,
            'schemas': True,
        }
        result = utils.bulk_delete_by_mappings(opts, None, [self.mapping_2])
        self.assertFalse(result['schemas']['Person']['is_unique'])
        self.assertTrue(result['schemas']['Location']['is_unique'])
        self.assertTrue(result['schemas']['Location']['is_deleted'])
        self.assertEqual(result['entities']['total'], 0)
        self.assertNotIn('submissions', result)

    def test_bulk_delete_by_mappings_mappingset(self):
        opts = {
            'entities': True,
            'schemas': True,
            'submissions': True
        }
        result = utils.bulk_delete_by_mappings(opts, self.mappingset_id)
        self.assertTrue(result['schemas']['Person']['is_unique'])
        self.assertTrue(result['schemas']['Location']['is_unique'])
        self.assertTrue(result['schemas']['Location']['is_deleted'])
        self.assertTrue(result['schemas']['Person']['is_deleted'])
        self.assertEqual(result['entities']['total'], 0)
        self.assertEqual(result['submissions'], 0)

        opts = {
            'entities': False,
            'schemas': False,
            'submissions': False
        }
        result = utils.bulk_delete_by_mappings(opts, self.mappingset_id)
        self.assertEqual(result, {})

    def test_bulk_delete_by_mappings_with_submissions(self):
        submission = {
            'id': str(uuid.uuid4()),
            'payload': dict(EXAMPLE_SOURCE_DATA_WITH_LOCATION),
            'project': str(self.project.id),
            'mappingset': self.mappingset_id,
        }
        self.client.post(
            reverse('submission-list'),
            data=submission,
            content_type='application/json',
        )
        # extract
        url = reverse('submission-extract', kwargs={'pk': submission['id']})
        self.client.patch(url)
        entity_count = models.Entity.objects.filter(
            mapping__id__in=[self.mapping_1, self.mapping_2]
        ).count()
        self.assertTrue(entity_count > 0)

        opts = {
            'entities': True,
            'submissions': True
        }
        result = utils.bulk_delete_by_mappings(opts, self.mappingset_id)
        self.assertEqual(result['entities']['total'], entity_count)
        self.assertEqual(result['submissions'], 1)
