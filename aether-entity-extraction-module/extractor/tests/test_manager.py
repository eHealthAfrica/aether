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
import uuid

from requests.exceptions import HTTPError
from queue import Queue

from unittest import TestCase, mock

from aether.python.entity.extractor import (
    ENTITY_EXTRACTION_ERRORS,
    ENTITY_EXTRACTION_ENRICHMENT,
)

from extractor.manager import (
    SUBMISSION_EXTRACTION_FLAG,
    SUBMISSION_PAYLOAD_FIELD,
    SUBMISSION_ENTITIES_FIELD,
    entity_extraction,
    get_prepared,
    push_to_kernel,
)

from extractor.utils import (
    ARTEFACT_NAMES,
    CacheType,
    Task,
    cache_has_object,
    count_quarantined,
    get_failed_objects,
    get_from_redis_or_kernel,
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

        submission = copy.deepcopy(SUBMISSION)
        submission['id'] = str(uuid.uuid4())
        self.submission_task = Task(
            id=submission['id'],
            data=submission,
            type=f'_{SUBMISSION_CHANNEL}',
            tenant=TENANT,
        )

    def helper__initial_extraction(self):
        # test extraction with missing schema definition in schema decorator
        self.assertEqual(len(SCHEMA_DECORATORS), 3)

        # remove the definition for one of the schema decorators
        sd = copy.deepcopy(SCHEMA_DECORATORS)[1]
        sd.pop(ARTEFACT_NAMES.schema_definition)
        self.redis.set(
            build_redis_key(ARTEFACT_NAMES.schemadecorators, TENANT, sd['id']),
            json.dumps(sd)
        )

        sub_queue = Queue()
        self.assertEqual(entity_extraction(self.submission_task, sub_queue, self.redis), 1)
        self.assertEqual(sub_queue.qsize(), 1)
        return sub_queue

    def test_entity_extraction(self):
        sub_queue = self.helper__initial_extraction()

        tenant, submission = sub_queue.get_nowait()
        self.assertEqual(tenant, TENANT)
        self.assertTrue(submission[SUBMISSION_EXTRACTION_FLAG])
        self.assertIn(ENTITY_EXTRACTION_ENRICHMENT, submission[SUBMISSION_PAYLOAD_FIELD])
        self.assertNotIn(ENTITY_EXTRACTION_ERRORS, submission[SUBMISSION_PAYLOAD_FIELD])
        self.assertIn(SUBMISSION_ENTITIES_FIELD, submission)
        self.assertEqual(len(submission[SUBMISSION_ENTITIES_FIELD]), 3)

        # included in cache
        self.assertEqual(cache_has_object(submission['id'], tenant, self.redis), CacheType.NORMAL)

    def test_entity_extraction__conform_no_mapping(self):
        sub_queue = Queue()
        task = Task(
            id=str(uuid.uuid4()),
            data=WRONG_SUBMISSION_PAYLOAD,
            type=f'_{SUBMISSION_CHANNEL}',
            tenant=TENANT,
        )

        self.assertEqual(entity_extraction(task, sub_queue, self.redis), 1)
        self.assertEqual(sub_queue.qsize(), 1)

        tenant, submission = sub_queue.get_nowait()
        self.assertEqual(tenant, TENANT)
        self.assertTrue(submission[SUBMISSION_EXTRACTION_FLAG], submission)
        self.assertNotIn(ENTITY_EXTRACTION_ENRICHMENT, submission[SUBMISSION_PAYLOAD_FIELD])
        self.assertNotIn(ENTITY_EXTRACTION_ERRORS, submission[SUBMISSION_PAYLOAD_FIELD])
        self.assertIn(SUBMISSION_ENTITIES_FIELD, submission)
        self.assertEqual(len(submission[SUBMISSION_ENTITIES_FIELD]), 0)

        # included in cache
        self.assertEqual(cache_has_object(submission['id'], tenant, self.redis), CacheType.NORMAL)

    def test_entity_extraction__unknown_mapping(self):
        sub_queue = Queue()
        task = Task(
            id=str(uuid.uuid4()),
            data=WRONG_SUBMISSION_MAPPING,
            type=f'_{SUBMISSION_CHANNEL}',
            tenant=TENANT,
        )

        self.assertEqual(entity_extraction(task, sub_queue, self.redis), 0)
        self.assertEqual(sub_queue.qsize(), 1)

        tenant, submission = sub_queue.get_nowait()
        self.assertEqual(tenant, TENANT)
        self.assertFalse(submission[SUBMISSION_EXTRACTION_FLAG])
        self.assertNotIn(ENTITY_EXTRACTION_ENRICHMENT, submission[SUBMISSION_PAYLOAD_FIELD])
        self.assertIn(ENTITY_EXTRACTION_ERRORS, submission[SUBMISSION_PAYLOAD_FIELD])
        self.assertNotIn(SUBMISSION_ENTITIES_FIELD, submission)

        # included in cache
        self.assertEqual(cache_has_object(submission['id'], tenant, self.redis), CacheType.NORMAL)

    def test_push_submissions_to_kernel(self):
        def _mock_fn_side_effect(url='', method='get', data=None, headers=None, realm=None):
            # different responses depending on data
            if any([x for x in data if x['id'] == '2']):
                raise HTTPError(response=mock.Mock(status_code=400))
            return

        _obj_t1 = {'id': '1', 'name': 'test 1'}
        _obj_t2 = {'id': '2', 'name': 'test 2'}
        sub_queue = Queue()
        sub_queue.put(tuple([TENANT, _obj_t1]))
        sub_queue.put(tuple([TENANT_2, _obj_t1]))
        sub_queue.put(tuple([TENANT_2, _obj_t2]))

        prepared = get_prepared(sub_queue, self.redis)
        self.assertEqual(sub_queue.qsize(), 0)
        self.assertEqual(dict(prepared), {TENANT: [_obj_t1], TENANT_2: [_obj_t1, _obj_t2]})

        with mock.patch('extractor.utils.kernel_data_request') as _mock_fn:
            _mock_fn.side_effect = _mock_fn_side_effect
            # emulate worker
            for realm, objs in prepared.items():
                push_to_kernel(realm, objs, sub_queue, self.redis)

            _mock_fn.assert_has_calls([
                mock.call(
                    url='submissions.json',
                    method='patch',
                    data=[_obj_t1],
                    realm=TENANT,
                ),
                mock.call(
                    url='submissions.json',
                    method='patch',
                    data=[_obj_t1, _obj_t2],
                    realm=TENANT_2,
                ),
                # halve_iteration chunks
                mock.call(
                    url='submissions.json',
                    method='patch',
                    data=[_obj_t1],
                    realm=TENANT_2,
                ),
                mock.call(
                    url='submissions.json',
                    method='patch',
                    data=[_obj_t2],
                    realm=TENANT_2,
                ),
            ])

        self.assertEqual(count_quarantined(self.redis), 1)
        q = Queue()
        get_failed_objects(q, self.redis)
        self.assertEqual(q.qsize(), 0)

    def test_workflow(self):
        sub_queue = self.helper__initial_extraction()

        prepared = get_prepared(sub_queue, self.redis)
        self.assertEqual(sub_queue.qsize(), 0)
        self.assertIn(TENANT, dict(prepared))

        with mock.patch('extractor.utils.kernel_data_request') as _mock_fn:
            # emulate worker
            for realm, objs in prepared.items():
                push_to_kernel(realm, objs, sub_queue, self.redis)

            _mock_fn.assert_has_calls([
                mock.call(
                    url='submissions.json',
                    method='patch',
                    data=prepared[TENANT],
                    realm=TENANT,
                ),
            ])

        # no errors/quarantine
        self.assertEqual(count_quarantined(self.redis), 0)
        q = Queue()
        get_failed_objects(q, self.redis)
        self.assertEqual(q.qsize(), 0)
        self.assertEqual(sub_queue.qsize(), 0)

    def test_workflow__error(self):
        sub_queue = self.helper__initial_extraction()

        prepared = get_prepared(sub_queue, self.redis)
        self.assertEqual(sub_queue.qsize(), 0)
        self.assertIn(TENANT, dict(prepared))

        with mock.patch('extractor.utils.kernel_data_request') as _mock_fn:
            _mock_fn.side_effect = HTTPError(response=mock.Mock(status_code=500))
            # emulate worker
            for realm, objs in prepared.items():
                push_to_kernel(realm, objs, sub_queue, self.redis)

            _mock_fn.assert_has_calls([
                mock.call(
                    url='submissions.json',
                    method='patch',
                    data=prepared[TENANT],
                    realm=TENANT,
                ),
            ])

        self.assertEqual(count_quarantined(self.redis), 0)
        q = Queue()
        get_failed_objects(q, self.redis)
        self.assertEqual(q.qsize(), 1)
        self.assertEqual(sub_queue.qsize(), 1)

    def test_workflow__quarantine(self):
        sub_queue = self.helper__initial_extraction()

        prepared = get_prepared(sub_queue, self.redis)
        self.assertEqual(sub_queue.qsize(), 0)
        self.assertIn(TENANT, dict(prepared))

        with mock.patch('extractor.utils.kernel_data_request') as _mock_fn:
            _mock_fn.side_effect = HTTPError(response=mock.Mock(status_code=400))
            # emulate worker
            for realm, objs in prepared.items():
                push_to_kernel(realm, objs, sub_queue, self.redis)

            _mock_fn.assert_has_calls([
                mock.call(
                    url='submissions.json',
                    method='patch',
                    data=prepared[TENANT],
                    realm=TENANT,
                ),
            ])

        # no errors but quarantine
        self.assertEqual(count_quarantined(self.redis), 1)
        q = Queue()
        get_failed_objects(q, self.redis)
        self.assertEqual(q.qsize(), 0)
        self.assertEqual(sub_queue.qsize(), 0)
