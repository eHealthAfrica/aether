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
import json
import uuid
import copy
import requests
from unittest import TestCase, mock
from ..manager import ExtractionManager
from . import MAPPINGS, MAPPINGSET, TENANT, SCHEMA_DECORATORS, SCHEMAS, SUBMISSION
from ..utils import KERNEL_ARTEFACT_NAMES, Task

import fakeredis

SUBMISSION_CHANNEL = 'test_submissions'


def build_key(_type, tenant, id):
    return f'_{_type}:{tenant}:{id}'


def load_redis(redis):
    # load mappingset
    redis.set(
        build_key(KERNEL_ARTEFACT_NAMES.mappingsets, TENANT, MAPPINGSET['id']),
        json.dumps(MAPPINGSET)
    )

    # load mappings
    [
        redis.set(
            build_key(KERNEL_ARTEFACT_NAMES.mappings, TENANT, m['id']),
            json.dumps(m)
        )
        for m in MAPPINGS
    ]

    # load schemas
    [
        redis.set(
            build_key(KERNEL_ARTEFACT_NAMES.schemas, TENANT, s['id']),
            json.dumps(s)
        )
        for s in SCHEMAS
    ]

    # load schema decorators
    [
        redis.set(
            build_key(KERNEL_ARTEFACT_NAMES.schemadecorators, TENANT, sd['id']),
            json.dumps(sd)
        )
        for sd in SCHEMA_DECORATORS
    ]


class ExtractionManagerTests(TestCase):
    redis = fakeredis.FakeStrictRedis()
    NO_OF_SUBMISSIONS = 10
    data = SUBMISSION
    data['id'] = str(uuid.uuid4())
    test_task = Task(
        id=data['id'],
        data=data,
        type=f'_{SUBMISSION_CHANNEL}',
        tenant=TENANT
    )

    def test_init_extraction_manager(self):
        manager = ExtractionManager()
        self.assertEqual(manager.SUBMISSION_QUEUE, collections.deque())
        self.assertEqual(manager.PROCESSED_SUBMISSIONS, collections.deque())
        self.assertEqual(manager.PROCESSED_ENTITIES, collections.deque())
        self.assertFalse(manager.is_extracting)
        self.assertFalse(manager.is_pushing_to_kernel)
        self.assertIsNone(manager.redis)

    def test_handle_pending_submissions(self):
        load_redis(self.redis)
        self.assertEqual(len(self.redis.execute_command('keys', '*')), 9)

        manager = ExtractionManager(self.redis)
        self.assertIsNotNone(manager.redis, None)

        # make submissions
        for x in range(self.NO_OF_SUBMISSIONS):
            SUBMISSION['id'] = str(uuid.uuid4())
            key = build_key(SUBMISSION_CHANNEL, TENANT, SUBMISSION['id'])
            publish_key = f'__keyspace@0__:{key}'
            data = json.dumps(SUBMISSION)
            self.redis.set(key, data)
            self.redis.publish(
                publish_key,
                data
            )

        self.assertEqual(
            len(self.redis.execute_command('keys', f'_{SUBMISSION_CHANNEL}*')),
            self.NO_OF_SUBMISSIONS
        )
        self.assertEqual(len(manager.SUBMISSION_QUEUE), 0)
        manager.handle_pending_submissions(f'_{SUBMISSION_CHANNEL}*')
        self.assertNotEqual(len(manager.SUBMISSION_QUEUE), 0)

    def test_add_to_queue(self):
        manager = ExtractionManager(self.redis)
        manager.add_to_queue(None)
        self.assertFalse(manager.is_extracting)
        self.assertIsNone(manager.push_to_kernel_thread)
        self.assertIsNone(manager.extraction_thread)

        manager.add_to_queue(self.test_task)
        self.assertTrue(manager.is_extracting)
        self.assertIsNotNone(manager.push_to_kernel_thread)
        self.assertIsNotNone(manager.extraction_thread)
        self.assertTrue(manager.push_to_kernel_thread.is_alive())
        self.assertTrue(manager.extraction_thread.is_alive())

    def test_entity_extraction(self):
        load_redis(self.redis)
        manager = ExtractionManager(self.redis)
        self.assertEqual(len(manager.PROCESSED_SUBMISSIONS), 0)
        self.assertEqual(len(manager.PROCESSED_ENTITIES), 0)
        # test extraction with missing schema definition in schema decorator
        remove_definitions = copy.deepcopy(SCHEMA_DECORATORS)
        for sd in remove_definitions:
            sd.pop(KERNEL_ARTEFACT_NAMES.schema_definition)
            self.redis.set(
                build_key(KERNEL_ARTEFACT_NAMES.schemadecorators, TENANT, sd['id']),
                json.dumps(sd)
            )
        manager.entity_extraction(self.test_task)
        self.assertEqual(len(manager.PROCESSED_SUBMISSIONS), 1)
        self.assertEqual(len(manager.PROCESSED_ENTITIES), 3)

    @mock.patch(
        'extractor.utils.kernel_data_request'
    )
    def test_push_to_kernel(self, mock_kernel_data_request):
        mock_response = requests.Response()
        mock_response.status_code = 500
        mock_kernel_data_request.return_value = mock_response
        manager = ExtractionManager()
        manager.PROCESSED_ENTITIES.appendleft({'name': 'test entity'})
        manager.PROCESSED_SUBMISSIONS.appendleft({
            'name': 'test submission',
            'tenant': TENANT,
            'id': 'id_1',
            'mappings': ['1', '2']
        })
        manager.push_to_kernel()
