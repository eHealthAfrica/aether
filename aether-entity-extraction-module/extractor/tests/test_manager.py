# Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
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

import collections
import fakeredis
import json
import uuid
import copy

from unittest import TestCase, mock

from ..manager import ExtractionManager
from ..utils import (
    KERNEL_ARTEFACT_NAMES,
    Task,
)

from . import (
    MAPPINGS,
    MAPPINGSET,
    TENANT,
    SCHEMA_DECORATORS,
    SCHEMAS,
    SUBMISSION,
    WRONG_SUBMISSION,
    SUBMISSION_WRONG_MAPPING
)

SUBMISSION_CHANNEL = 'test_submissions'


def build_redis_key(_type, tenant, id):
    return f'_{_type}:{tenant}:{id}'


def load_redis(redis):
    # load mappingset
    redis.set(
        build_redis_key(KERNEL_ARTEFACT_NAMES.mappingsets, TENANT, MAPPINGSET['id']),
        json.dumps(MAPPINGSET)
    )

    # load mappings
    [
        redis.set(
            build_redis_key(KERNEL_ARTEFACT_NAMES.mappings, TENANT, m['id']),
            json.dumps(m)
        )
        for m in MAPPINGS
    ]

    # load schemas
    [
        redis.set(
            build_redis_key(KERNEL_ARTEFACT_NAMES.schemas, TENANT, s['id']),
            json.dumps(s)
        )
        for s in SCHEMAS
    ]

    # load schema decorators
    [
        redis.set(
            build_redis_key(KERNEL_ARTEFACT_NAMES.schemadecorators, TENANT, sd['id']),
            json.dumps(sd)
        )
        for sd in SCHEMA_DECORATORS
    ]


class ExtractionManagerTests(TestCase):

    def setUp(self):
        super(ExtractionManagerTests, self).setUp()

        data = copy.deepcopy(SUBMISSION)
        data['id'] = str(uuid.uuid4())

        self.test_task = Task(
            id=data['id'],
            data=data,
            type=f'_{SUBMISSION_CHANNEL}',
            tenant=TENANT,
        )

        self.redis = fakeredis.FakeStrictRedis()
        load_redis(self.redis)

        self.manager = ExtractionManager(self.redis)
        self.assertIsNotNone(self.manager.redis, None)

    def test_init_extraction_manager(self):
        manager = ExtractionManager()
        self.assertIsNone(manager.redis)
        self.assertEqual(manager.SUBMISSION_QUEUE, collections.deque())
        self.assertEqual(manager.PROCESSED_SUBMISSIONS, collections.deque())
        self.assertEqual(manager.realm_entities, {})
        self.assertFalse(manager.is_extracting)
        self.assertFalse(manager.is_pushing_to_kernel)

    def test_handle_pending_submissions(self):
        self.assertEqual(len(self.redis.execute_command('keys', '*')), 9)

        # make submissions
        NO_OF_SUBMISSIONS = 10
        for x in range(NO_OF_SUBMISSIONS):
            SUBMISSION['id'] = str(uuid.uuid4())
            key = build_redis_key(SUBMISSION_CHANNEL, TENANT, SUBMISSION['id'])
            publish_key = f'__keyspace@0__:{key}'
            data = json.dumps(SUBMISSION)
            self.redis.set(key, data)
            self.redis.publish(publish_key, data)

        self.assertEqual(
            len(self.redis.execute_command('keys', f'_{SUBMISSION_CHANNEL}*')),
            NO_OF_SUBMISSIONS
        )
        self.assertEqual(len(self.manager.SUBMISSION_QUEUE), 0)

        self.manager.handle_pending_submissions(f'_{SUBMISSION_CHANNEL}*')
        self.assertNotEqual(len(self.manager.SUBMISSION_QUEUE), 0)

    def test_add_to_queue(self):
        self.manager.add_to_queue(None)
        self.assertFalse(self.manager.is_extracting)
        self.assertIsNone(self.manager.push_to_kernel_thread)
        self.assertIsNone(self.manager.extraction_thread)

        self.manager.add_to_queue(self.test_task)
        self.assertTrue(self.manager.is_extracting)
        self.assertIsNotNone(self.manager.push_to_kernel_thread)
        self.assertIsNotNone(self.manager.extraction_thread)
        self.assertTrue(self.manager.push_to_kernel_thread.is_alive())
        self.assertTrue(self.manager.extraction_thread.is_alive())

    def test_entity_extraction(self):
        self.assertEqual(len(self.manager.PROCESSED_SUBMISSIONS), 0)
        self.assertEqual(self.manager.realm_entities, {})

        # test extraction with missing schema definition in schema decorator
        remove_definitions = copy.deepcopy(SCHEMA_DECORATORS)
        for sd in remove_definitions:
            sd.pop(KERNEL_ARTEFACT_NAMES.schema_definition)
            self.redis.set(
                build_redis_key(KERNEL_ARTEFACT_NAMES.schemadecorators, TENANT, sd['id']),
                json.dumps(sd)
            )

        self.manager.entity_extraction(self.test_task)
        self.assertEqual(len(self.manager.PROCESSED_SUBMISSIONS), 1)
        self.assertEqual(len(self.manager.realm_entities[TENANT]), 3)

    def test_entity_extraction__error(self):
        wrong_task = Task(
            id=str(uuid.uuid4()),
            data=WRONG_SUBMISSION,
            type=f'_{SUBMISSION_CHANNEL}',
            tenant=TENANT,
        )
        self.assertEqual(len(self.manager.PROCESSED_SUBMISSIONS), 0)
        self.manager.entity_extraction(wrong_task)
        self.assertEqual(len(self.manager.PROCESSED_SUBMISSIONS), 1)
        self.assertNotIn(TENANT, self.manager.realm_entities)

        wrong_mapping_task = Task(
            id=str(uuid.uuid4()),
            data=SUBMISSION_WRONG_MAPPING,
            type=f'_{SUBMISSION_CHANNEL}',
            tenant=TENANT,
        )
        self.manager.entity_extraction(wrong_mapping_task)
        self.assertEqual(len(self.manager.PROCESSED_SUBMISSIONS), 2)
        self.assertNotIn(TENANT, self.manager.realm_entities)

    @mock.patch('extractor.manager.kernel_data_request', return_value={})
    @mock.patch('extractor.manager.cache_failed_entities')
    def test_push_to_kernel(self, mock_cache_failed_entities, mock_kernel_data_request):
        self.manager.realm_entities[TENANT] = collections.deque()
        self.manager.realm_entities[TENANT].appendleft({'name': 'test entity', 'submission': 'id_1'})
        self.manager.PROCESSED_SUBMISSIONS.appendleft({
            'name': 'test submission',
            'tenant': TENANT,
            'id': 'id_1',
            'mappings': ['1', '2']
        })

        self.manager.push_to_kernel()

        mock_kernel_data_request.assert_has_calls([
            mock.call(
                url='entities/',
                method='post',
                data=[{'name': 'test entity', 'submission': 'id_1'}],
                realm=TENANT,
            ),
            mock.call(
                url='submissions/bulk_update_extracted/',
                method='patch',
                data=[{'name': 'test submission', 'id': 'id_1'}],
            ),
        ])
        mock_cache_failed_entities.assert_not_called()

    @mock.patch('extractor.manager.kernel_data_request', side_effect=Exception)
    def test_push_to_kernel__error(self, mock_kernel_data_request):
        self.manager.realm_entities[TENANT] = collections.deque()
        self.manager.realm_entities[TENANT].appendleft({'name': 'test entity', 'submission': 'id_1'})
        self.manager.PROCESSED_SUBMISSIONS.appendleft({
            'name': 'test submission',
            'tenant': TENANT,
            'id': 'id_1',
            'mappings': ['1', '2']
        })

        self.manager.push_to_kernel()

        mock_kernel_data_request.assert_has_calls([
            mock.call(
                url='entities/',
                method='post',
                data=[{'name': 'test entity', 'submission': 'id_1'}],
                realm=TENANT,
            ),
            mock.call(
                url='submissions/bulk_update_extracted/',
                method='patch',
                data=[{'name': 'test submission', 'id': 'id_1'}],
            ),
        ])
