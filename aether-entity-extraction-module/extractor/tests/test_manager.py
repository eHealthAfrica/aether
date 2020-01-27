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

import copy
import fakeredis
import json
from queue import Queue
import uuid

from unittest import TestCase, mock

from aether.python.entity.extractor import (
    ENTITY_EXTRACTION_ERRORS,
    ENTITY_EXTRACTION_ENRICHMENT,
)

from extractor.manager import (
    ExtractionManager, entity_extraction, push_to_kernel, get_prepared
)
from extractor.utils import (
    Artifact,
    ARTEFACT_NAMES,
    SUBMISSION_EXTRACTION_FLAG,
    SUBMISSION_PAYLOAD_FIELD,
    Task,
    cache_has_object,
    CacheType,
    get_failed_objects,
    get_from_redis_or_kernel,
    get_redis_keys_by_pattern,
    remove_from_cache,
    quarantine,
    count_quarantined
)
from extractor import settings

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


logger = settings.get_logger('UnitTest')


def build_redis_key(_type, tenant, id):
    return f'_{_type}:{tenant}:{id}'


def load_redis(redis):
    # load mappingset
    redis.set(
        build_redis_key(ARTEFACT_NAMES.mappingsets, TENANT, MAPPINGSET['id']),
        json.dumps(MAPPINGSET)
    )
    assert(
        get_from_redis_or_kernel(
            id=MAPPINGSET['id'],
            model_type=ARTEFACT_NAMES.mappingsets,
            tenant=TENANT,
            redis=redis
        ) is not None)

    # load mappings
    for m in MAPPINGS:
        redis.set(
            build_redis_key(ARTEFACT_NAMES.mappings, TENANT, m['id']),
            json.dumps(m)
        )
        assert(
            get_from_redis_or_kernel(
                id=m['id'],
                model_type=ARTEFACT_NAMES.mappings,
                tenant=TENANT,
                redis=redis
            ) is not None)

    # load schemas
    for s in SCHEMAS:
        redis.set(
            build_redis_key(ARTEFACT_NAMES.schemas, TENANT, s['id']),
            json.dumps(s)
        )
        assert(
            get_from_redis_or_kernel(
                id=s['id'],
                model_type=ARTEFACT_NAMES.schemas,
                tenant=TENANT,
                redis=redis
            ) is not None)

    # load schema decorators
    for sd in SCHEMA_DECORATORS:
        redis.set(
            build_redis_key(ARTEFACT_NAMES.schemadecorators, TENANT, sd['id']),
            json.dumps(sd)
        )
        assert(
            get_from_redis_or_kernel(
                id=sd['id'],
                model_type=ARTEFACT_NAMES.schemadecorators,
                tenant=TENANT,
                redis=redis
            ) is not None)


class ExtractionManagerTests(TestCase):

    def setUp(self):
        super(ExtractionManagerTests, self).setUp()

        self.redis = fakeredis.FakeStrictRedis()
        load_redis(self.redis)
        logger.info('New Redis')
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
        # remove failed
        logger.info('Teardown...')
        try:
            self.manager.stop()
        except Exception:
            pass
        super(ExtractionManagerTests, self).tearDown()

    def test_init_extraction_manager(self):
        self.assertIsNotNone(self.manager.redis)
        self.assertEqual(self.manager.processed_submissions.qsize(), 0)
        self.assertEqual(self.manager.extracted_entities.qsize(), 0)

    def test_handle_pending_submissions(self):
        NO_OF_SUBMISSIONS = 10

        self.assertEqual(len(self.redis.execute_command('keys', '*')), 9)

        # make submissions
        for x in range(NO_OF_SUBMISSIONS):
            submission = copy.deepcopy(SUBMISSION)
            submission['id'] = str(uuid.uuid4())
            key = build_redis_key(SUBMISSION_CHANNEL, TENANT, submission['id'])

            data = json.dumps(submission)
            self.redis.set(key, data)
            self.redis.publish(f'__keyspace@0__:{key}', data)

        self.assertEqual(
            len(self.redis.execute_command('keys', f'_{SUBMISSION_CHANNEL}*')),
            NO_OF_SUBMISSIONS
        )

    def test_add_to_queue(self):
        self.manager.add_to_queue(None)
        self.assertEqual(self.manager.processed_submissions.qsize(), 0)

        self.manager.add_to_queue(self.submission_task)
        self.assertNotEqual(self.manager.processed_submissions.get(), None)
        # remove signal from Redis
        for key in get_redis_keys_by_pattern(SUBMISSION_CHANNEL, self.redis):
            self.redis.delete(key)
        self.assertEqual(len(get_redis_keys_by_pattern(SUBMISSION_CHANNEL, self.redis)), 0)

    def test_entity_extraction(self):
        # test extraction with missing schema definition in schema decorator
        self.assertEqual(len(SCHEMA_DECORATORS), 3)
        remove_definitions = copy.deepcopy(SCHEMA_DECORATORS)
        for sd in remove_definitions:
            sd.pop(ARTEFACT_NAMES.schema_definition)
            self.redis.set(
                build_redis_key(ARTEFACT_NAMES.schemadecorators, TENANT, sd['id']),
                json.dumps(sd)
            )
        sub_queue = Queue()
        entity_queue = Queue()

        self.assertEqual(entity_extraction(
            self.submission_task,
            entity_queue,
            sub_queue,
            self.redis), 1)

        self.assertEqual(sub_queue.qsize(), 1)
        self.assertEqual(entity_queue.qsize(), 3)

        tenant, submission = sub_queue.get_nowait()
        self.assertEqual(tenant, TENANT)
        self.assertTrue(submission[SUBMISSION_EXTRACTION_FLAG])
        self.assertIn(ENTITY_EXTRACTION_ENRICHMENT, submission[SUBMISSION_PAYLOAD_FIELD])
        self.assertNotIn(ENTITY_EXTRACTION_ERRORS, submission[SUBMISSION_PAYLOAD_FIELD])

    def test_entity_extraction__conform_no_mapping(self):
        sub_queue = Queue()
        entity_queue = Queue()
        task = Task(
            id=str(uuid.uuid4()),
            data=WRONG_SUBMISSION_PAYLOAD,
            type=f'_{SUBMISSION_CHANNEL}',
            tenant=TENANT,
        )

        self.assertEqual(
            entity_extraction(
                task,
                entity_queue,
                sub_queue,
                self.redis), 1)

        self.assertEqual(sub_queue.qsize(), 1)
        self.assertEqual(entity_queue.qsize(), 0)

        tenant, submission = sub_queue.get_nowait()

        self.assertEqual(tenant, TENANT)
        self.assertTrue(submission[SUBMISSION_EXTRACTION_FLAG], submission)
        self.assertNotIn(ENTITY_EXTRACTION_ENRICHMENT, submission[SUBMISSION_PAYLOAD_FIELD])
        self.assertNotIn(ENTITY_EXTRACTION_ERRORS, submission[SUBMISSION_PAYLOAD_FIELD])

    def test_entity_extraction__unknown_mapping(self):
        sub_queue = Queue()
        entity_queue = Queue()
        task = Task(
            id=str(uuid.uuid4()),
            data=WRONG_SUBMISSION_MAPPING,
            type=f'_{SUBMISSION_CHANNEL}',
            tenant=TENANT,
        )

        self.assertEqual(
            entity_extraction(
                task,
                entity_queue,
                sub_queue,
                self.redis), 0)

        self.assertEqual(sub_queue.qsize(), 1)
        self.assertEqual(entity_queue.qsize(), 0)

        tenant, submission = sub_queue.get_nowait()
        self.assertEqual(tenant, TENANT)
        self.assertFalse(submission[SUBMISSION_EXTRACTION_FLAG])
        self.assertNotIn(ENTITY_EXTRACTION_ENRICHMENT, submission[SUBMISSION_PAYLOAD_FIELD])
        self.assertIn(ENTITY_EXTRACTION_ERRORS, submission[SUBMISSION_PAYLOAD_FIELD])

    @mock.patch('extractor.manager.kernel_data_request', return_value=list)
    # @mock.patch('extractor.manager.cache_failed_entities')
    def test_push_entities_to_kernel(self, mock_kernel_data_request):  # mock_cache_failed_entities
        _obj_t1 = [{'id': 'test_push_entities_to_kernel1', 'name': 'test entity 1'}]
        _obj_t2 = [{'id': 'test_push_entities_to_kernel2', 'name': 'test entity 2'}]

        push_to_kernel(Artifact.ENTITY, TENANT, _obj_t1, self.manager.extracted_entities)
        push_to_kernel(Artifact.ENTITY, TENANT_2, _obj_t2, self.manager.extracted_entities)
        mock_kernel_data_request.assert_has_calls([
            mock.call(
                url='entities.json',
                method='post',
                data=[{'id': 'test_push_entities_to_kernel1', 'name': 'test entity 1'}],
                realm=TENANT,
            ),
            mock.call(
                url='entities.json',
                method='post',
                data=[{'id': 'test_push_entities_to_kernel2', 'name': 'test entity 2'}],
                realm=TENANT_2,
            ),
        ])
        # mock_cache_failed_entities.assert_not_called()

    # @mock.patch('extractor.manager.kernel_data_request')  #, side_effect=Exception)
    @mock.patch('extractor.manager.kernel_data_request')
    def test_push_entities_to_kernel__error(self, mock_kernel_data_request):
        _obj_t1 = [{'id': 'test_push_entities_to_kernel__error1', 'name': 'test entity 1'}]
        _obj_t2 = [{'id': 'test_push_entities_to_kernel__error2', 'name': 'test entity 2'}]

        push_to_kernel(Artifact.ENTITY, TENANT, _obj_t1, self.manager.extracted_entities)
        push_to_kernel(Artifact.ENTITY, TENANT_2, _obj_t2, self.manager.extracted_entities)

        mock_kernel_data_request.assert_has_calls([
            mock.call(
                url='entities.json',
                method='post',
                data=[{'id': 'test_push_entities_to_kernel__error1', 'name': 'test entity 1'}],
                realm=TENANT,
            ),
            mock.call(
                url='entities.json',
                method='post',
                data=[{'id': 'test_push_entities_to_kernel__error2', 'name': 'test entity 2'}],
                realm=TENANT_2,
            ),
        ])

    @mock.patch('extractor.manager.kernel_data_request', return_value=list)
    def test_push_submissions_to_kernel(self, mock_kernel_data_request):
        _obj_t1 = [{'id': 'test_push_submissions_to_kernel1', 'name': 'test submission 1'}]
        _obj_t2 = [{'id': 'test_push_submissions_to_kernel2', 'name': 'test submission 2'}]

        push_to_kernel(Artifact.SUBMISSION, TENANT, _obj_t1, self.manager.processed_submissions)
        push_to_kernel(Artifact.SUBMISSION, TENANT_2, _obj_t2, self.manager.processed_submissions)

        mock_kernel_data_request.assert_has_calls([
            mock.call(
                url='submissions/bulk_update_extracted.json',
                method='patch',
                data=[{'id': 'test_push_submissions_to_kernel1', 'name': 'test submission 1'}],
                realm=TENANT,
            ),
            mock.call(
                url='submissions/bulk_update_extracted.json',
                method='patch',
                data=[{'id': 'test_push_submissions_to_kernel2', 'name': 'test submission 2'}],
                realm=TENANT_2,
            ),
        ])

    @mock.patch('extractor.manager.kernel_data_request')  # , side_effect=Exception)
    def test_push_submissions_to_kernel__error(self, mock_kernel_data_request):

        _obj_t1 = [{'id': 'test_push_submissions_to_kernel__error1', 'name': 'test submission 1'}]
        _obj_t2 = [{'id': 'test_push_submissions_to_kernel__error2', 'name': 'test submission 2'}]

        push_to_kernel(Artifact.SUBMISSION, TENANT, _obj_t1, self.manager.processed_submissions)
        push_to_kernel(Artifact.SUBMISSION, TENANT_2, _obj_t2, self.manager.processed_submissions)

        mock_kernel_data_request.assert_has_calls([
            mock.call(
                url='submissions/bulk_update_extracted.json',
                method='patch',
                data=[{'id': 'test_push_submissions_to_kernel__error1', 'name': 'test submission 1'}],
                realm=TENANT,
            ),
            mock.call(
                url='submissions/bulk_update_extracted.json',
                method='patch',
                data=[{'id': 'test_push_submissions_to_kernel__error2', 'name': 'test submission 2'}],
                realm=TENANT_2,
            ),
        ])

    def test__get_prepared(self):
        e_queue = Queue()
        sub_queue = Queue()
        self.assertEqual(
            entity_extraction(
                self.submission_task,
                e_queue,
                sub_queue,
                self.redis
            ), 1)
        for q_in, _type in [(e_queue, Artifact.ENTITY), (sub_queue, Artifact.SUBMISSION)]:
            prepared = get_prepared(q_in, _type)
            self.assertEqual(push_to_kernel(_type, TENANT, prepared[TENANT], q_in), 0)
            self.assertEqual(count_quarantined(_type, self.redis), 0)
            q = Queue()
            get_failed_objects(q, _type, self.redis)
            self.assertTrue(q.qsize() > 0)
            realm, sample = q.get_nowait()
            self.assertEqual(
                cache_has_object(sample['id'], realm, _type, self.redis), CacheType.NORMAL)
            remove_from_cache(sample, realm, _type, self.redis)
            self.assertEqual(
                cache_has_object(sample['id'], realm, _type, self.redis), CacheType.NONE)
            quarantine([sample], realm, _type)
            self.assertEqual(count_quarantined(_type, self.redis), 0)
