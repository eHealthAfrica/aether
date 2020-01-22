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
import copy
import fakeredis
import json
import uuid

from unittest import TestCase, mock

from aether.python.entity.extractor import (
    ENTITY_EXTRACTION_ERRORS,
    ENTITY_EXTRACTION_ENRICHMENT,
)

from extractor.manager import ExtractionManager
from extractor.utils import (
    ARTEFACT_NAMES,
    SUBMISSION_EXTRACTION_FLAG,
    SUBMISSION_PAYLOAD_FIELD,
    Task,
)

from . import (
    MAPPINGS,
    MAPPINGSET,
    SCHEMA_DECORATORS,
    SCHEMAS,
    SUBMISSION,
    WRONG_SUBMISSION_MAPPING,
    WRONG_SUBMISSION_PAYLOAD,
)

SUBMISSION_CHANNEL = 'test_submissions'
TENANT = 'test'
TENANT_2 = 'test-2'


def build_redis_key(_type, tenant, id):
    return f'_{_type}:{tenant}:{id}'


def load_redis(redis):
    # load mappingset
    redis.set(
        build_redis_key(ARTEFACT_NAMES.mappingsets, TENANT, MAPPINGSET['id']),
        json.dumps(MAPPINGSET)
    )

    # load mappings
    for m in MAPPINGS:
        redis.set(
            build_redis_key(ARTEFACT_NAMES.mappings, TENANT, m['id']),
            json.dumps(m)
        )

    # load schemas
    for s in SCHEMAS:
        redis.set(
            build_redis_key(ARTEFACT_NAMES.schemas, TENANT, s['id']),
            json.dumps(s)
        )

    # load schema decorators
    for sd in SCHEMA_DECORATORS:
        redis.set(
            build_redis_key(ARTEFACT_NAMES.schemadecorators, TENANT, sd['id']),
            json.dumps(sd)
        )


class ExtractionManagerTests(TestCase):

    def setUp(self):
        super(ExtractionManagerTests, self).setUp()

        self.redis = fakeredis.FakeStrictRedis()
        load_redis(self.redis)

        self.manager = ExtractionManager(self.redis)
        self.assertIsNotNone(self.manager.redis)

        submission = copy.deepcopy(SUBMISSION)
        submission['id'] = str(uuid.uuid4())
        self.submission_task = Task(
            id=submission['id'],
            data=submission,
            type=f'_{SUBMISSION_CHANNEL}',
            tenant=TENANT,
        )

    def tearDown(self):
        self.manager.stop()
        super(ExtractionManagerTests, self).tearDown()

    def test_init_extraction_manager(self):
        manager = ExtractionManager()
        self.assertIsNone(manager.redis)

        self.assertEqual(manager.pending_submissions, collections.deque())
        self.assertEqual(manager.processed_submissions, {})
        self.assertEqual(manager.extracted_entities, {})

        self.assertFalse(manager.is_extracting)
        self.assertFalse(manager.is_pushing_to_kernel)

    def test_handle_pending_submissions(self):
        NO_OF_SUBMISSIONS = 10

        self.assertEqual(len(self.redis.execute_command('keys', '*')), 9)

        # make submissions
        for x in range(NO_OF_SUBMISSIONS):
            submission = copy.deepcopy(SUBMISSION)
            submission['id'] = str(uuid.uuid4())
            key = build_redis_key(SUBMISSION_CHANNEL, TENANT, submission['id'])
            publish_key = f'__keyspace@0__:{key}'
            data = json.dumps(submission)
            self.redis.set(key, data)
            self.redis.publish(publish_key, data)

        self.assertEqual(
            len(self.redis.execute_command('keys', f'_{SUBMISSION_CHANNEL}*')),
            NO_OF_SUBMISSIONS
        )
        self.assertEqual(len(self.manager.pending_submissions), 0)
        self.manager.handle_pending_submissions(f'_{SUBMISSION_CHANNEL}*')
        self.assertNotEqual(len(self.manager.pending_submissions), 0)

    def test_add_to_queue(self):
        self.manager.add_to_queue(None)
        self.assertFalse(self.manager.is_extracting)
        self.assertFalse(self.manager.is_pushing_to_kernel)

        self.manager.add_to_queue(self.submission_task)
        self.assertTrue(self.manager.is_extracting)
        self.assertTrue(self.manager.is_pushing_to_kernel)

    def test_entity_extraction(self):
        self.assertEqual(self.manager.processed_submissions, {})
        self.assertEqual(self.manager.extracted_entities, {})

        # test extraction with missing schema definition in schema decorator
        self.assertEqual(len(SCHEMA_DECORATORS), 3)
        remove_definitions = copy.deepcopy(SCHEMA_DECORATORS)
        for sd in remove_definitions:
            sd.pop(ARTEFACT_NAMES.schema_definition)
            self.redis.set(
                build_redis_key(ARTEFACT_NAMES.schemadecorators, TENANT, sd['id']),
                json.dumps(sd)
            )

        self.manager.entity_extraction(self.submission_task)
        self.assertEqual(len(self.manager.processed_submissions[TENANT]), 1)
        self.assertEqual(len(self.manager.extracted_entities[TENANT]), 3)

        submission = self.manager.processed_submissions[TENANT].pop()
        self.assertTrue(submission[SUBMISSION_EXTRACTION_FLAG])
        self.assertIn(ENTITY_EXTRACTION_ENRICHMENT, submission[SUBMISSION_PAYLOAD_FIELD])
        self.assertNotIn(ENTITY_EXTRACTION_ERRORS, submission[SUBMISSION_PAYLOAD_FIELD])

    def test_entity_extraction__conform_no_mapping(self):
        task = Task(
            id=str(uuid.uuid4()),
            data=WRONG_SUBMISSION_PAYLOAD,
            type=f'_{SUBMISSION_CHANNEL}',
            tenant=TENANT,
        )

        self.manager.entity_extraction(task)
        self.assertEqual(len(self.manager.processed_submissions[TENANT]), 1)
        self.assertNotIn(TENANT, self.manager.extracted_entities)

        submission = self.manager.processed_submissions[TENANT].pop()
        self.assertTrue(submission[SUBMISSION_EXTRACTION_FLAG], submission)
        self.assertNotIn(ENTITY_EXTRACTION_ENRICHMENT, submission[SUBMISSION_PAYLOAD_FIELD])
        self.assertNotIn(ENTITY_EXTRACTION_ERRORS, submission[SUBMISSION_PAYLOAD_FIELD])

    def test_entity_extraction__unknown_mapping(self):
        task = Task(
            id=str(uuid.uuid4()),
            data=WRONG_SUBMISSION_MAPPING,
            type=f'_{SUBMISSION_CHANNEL}',
            tenant=TENANT,
        )

        self.manager.entity_extraction(task)
        self.assertEqual(len(self.manager.processed_submissions[TENANT]), 1)
        self.assertNotIn(TENANT, self.manager.extracted_entities)

        submission = self.manager.processed_submissions[TENANT].pop()
        self.assertFalse(submission[SUBMISSION_EXTRACTION_FLAG])
        self.assertNotIn(ENTITY_EXTRACTION_ENRICHMENT, submission[SUBMISSION_PAYLOAD_FIELD])
        self.assertIn(ENTITY_EXTRACTION_ERRORS, submission[SUBMISSION_PAYLOAD_FIELD])

    @mock.patch('extractor.manager.kernel_data_request', return_value=list)
    @mock.patch('extractor.manager.cache_failed_entities')
    def test_push_entities_to_kernel(self, mock_cache_failed_entities, mock_kernel_data_request):
        self.manager.extracted_entities[TENANT] = collections.deque([{'name': 'test entity 1'}])
        self.manager.extracted_entities[TENANT_2] = collections.deque([{'name': 'test entity 2'}])

        self.manager.push_entities_to_kernel()

        mock_kernel_data_request.assert_has_calls([
            mock.call(
                url='entities.json',
                method='post',
                data=[{'name': 'test entity 1'}],
                realm=TENANT,
            ),
            mock.call(
                url='entities.json',
                method='post',
                data=[{'name': 'test entity 2'}],
                realm=TENANT_2,
            ),
        ])
        mock_cache_failed_entities.assert_not_called()

    @mock.patch('extractor.manager.kernel_data_request', side_effect=Exception)
    @mock.patch('extractor.manager.cache_failed_entities')
    def test_push_entities_to_kernel__error(self, mock_cache_failed_entities, mock_kernel_data_request):
        self.manager.extracted_entities[TENANT] = collections.deque([{'name': 'test entity 1'}])
        self.manager.extracted_entities[TENANT_2] = collections.deque([{'name': 'test entity 2'}])

        self.manager.push_entities_to_kernel()

        mock_kernel_data_request.assert_has_calls([
            mock.call(
                url='entities.json',
                method='post',
                data=[{'name': 'test entity 1'}],
                realm=TENANT,
            ),
            mock.call(
                url='entities.json',
                method='post',
                data=[{'name': 'test entity 2'}],
                realm=TENANT_2,
            ),
        ])
        mock_cache_failed_entities.assert_called()

    @mock.patch('extractor.manager.kernel_data_request', return_value=list)
    def test_push_submissions_to_kernel(self, mock_kernel_data_request):
        self.manager.processed_submissions[TENANT] = collections.deque([{'name': 'test submission 1'}])
        self.manager.processed_submissions[TENANT_2] = collections.deque([{'name': 'test submission 2'}])

        self.manager.push_submissions_to_kernel()

        mock_kernel_data_request.assert_has_calls([
            mock.call(
                url='submissions/bulk_update_extracted.json',
                method='patch',
                data=[{'name': 'test submission 1'}],
                realm=TENANT,
            ),
            mock.call(
                url='submissions/bulk_update_extracted.json',
                method='patch',
                data=[{'name': 'test submission 2'}],
                realm=TENANT_2,
            ),
        ])

    @mock.patch('extractor.manager.kernel_data_request', side_effect=Exception)
    def test_push_submissions_to_kernel__error(self, mock_kernel_data_request):
        self.manager.processed_submissions[TENANT] = collections.deque([{'name': 'test submission 1'}])
        self.manager.processed_submissions[TENANT_2] = collections.deque([{'name': 'test submission 2'}])

        self.manager.push_submissions_to_kernel()

        mock_kernel_data_request.assert_has_calls([
            mock.call(
                url='submissions/bulk_update_extracted.json',
                method='patch',
                data=[{'name': 'test submission 1'}],
                realm=TENANT,
            ),
            mock.call(
                url='submissions/bulk_update_extracted.json',
                method='patch',
                data=[{'name': 'test submission 2'}],
                realm=TENANT_2,
            ),
        ])
