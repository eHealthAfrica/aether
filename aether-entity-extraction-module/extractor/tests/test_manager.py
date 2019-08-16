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
# import time

from unittest import TestCase
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
        self.manager = ExtractionManager()
        self.assertEqual(self.manager.SUBMISSION_QUEUE, collections.deque())
        self.assertEqual(self.manager.PROCESSED_SUBMISSIONS, collections.deque())
        self.assertEqual(self.manager.PROCESSED_ENTITIES, collections.deque())
        self.assertFalse(self.manager.is_extracting)
        self.assertFalse(self.manager.is_pushing_to_kernel)
        self.assertIsNone(self.manager.redis)

    def test_handle_pending_submissions(self):
        load_redis(self.redis)
        self.assertEqual(len(self.redis.execute_command('keys', '*')), 9)

        self.manager = ExtractionManager(self.redis)
        self.assertIsNotNone(self.manager.redis, None)

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
        self.assertEqual(len(self.manager.SUBMISSION_QUEUE), 0)
        self.manager.handle_pending_submissions(f'_{SUBMISSION_CHANNEL}*')
        self.assertNotEqual(len(self.manager.SUBMISSION_QUEUE), 0)

        # subscribe to channel
        # self.manager.subscribe_to_redis_channel(
        #     self.manager.add_to_queue,
        #     f'_{SUBMISSION_CHANNEL}:*'
        # )

    def test_add_to_queue(self):
        self.manager = ExtractionManager(self.redis)
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
