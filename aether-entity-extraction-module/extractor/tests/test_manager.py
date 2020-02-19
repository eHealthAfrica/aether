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
import json
import uuid
import pytest
from time import sleep

from redis.exceptions import LockError
from requests.exceptions import HTTPError
from queue import Queue

from unittest import mock

from aether.python.redis.task import Task, TaskEvent
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

from extractor.utils import (  # noqa
    ARTEFACT_NAMES,
    CacheType,
    cache_has_object,
    count_quarantined,
    list_quarantined,
    count_failed_objects,
    list_failed_objects,
    get_failed_objects,
    get_from_redis_or_kernel,
)

from extractor import settings

from . import (
    SCHEMA_DECORATORS,
    WRONG_SUBMISSION_MAPPING,
    WRONG_SUBMISSION_PAYLOAD,
    build_redis_key
)

from . import *  # noqa  # have to import all for fixtures to work

SUBMISSION_CHANNEL = 'test_submissions'
TENANT = 'test'
TENANT_2 = 'test-2'


_logger = settings.get_logger('UNIT')


def test__manager_lock(manager_fn_scope):  # noqa  # pytest fixtures
    man = manager_fn_scope
    man._get_lock()
    with pytest.raises(LockError):
        man._get_lock(0.1)
    _meta = man.task_helper.get('lockmeta', man.LOCK_TYPE, '_all')
    assert _meta['owner'] == man._id


def test__manager_bad_event(manager_fn_scope, submission_task):
    man = manager_fn_scope
    assert man.add_to_queue(submission_task) is True
    bad = TaskEvent('a', 'b', 'c', 'd')
    assert man.add_to_queue(bad) is False


def test__manager_fail_on_locked(manager_fn_scope, submission_task):
    man = manager_fn_scope
    _lock = man._get_lock()
    # test old man dying
    man.start()
    sleep(6)
    assert man.is_alive() is not True
    _lock.release()


def test__manager_process_old(manager_fn_scope, submission_task):
    assert entity_extraction(submission_task, Queue()) == 1
    assert count_failed_objects() == 1, list_failed_objects()
    man = manager_fn_scope
    man.start()
    sleep(2)  # give it a second to work
    assert count_failed_objects() == 1, list_failed_objects()
    man.stop()


def test__manager_entity_extraction(redis_fn_scope, submission_task):
    redis = redis_fn_scope
    # test extraction with missing schema definition in schema decorator
    assert len(SCHEMA_DECORATORS) == 3
    remove_definitions = copy.deepcopy(SCHEMA_DECORATORS)
    for sd in remove_definitions:
        sd.pop(ARTEFACT_NAMES.schema_definition)
        redis.set(
            build_redis_key(ARTEFACT_NAMES.schemadecorators, TENANT, sd['id']),
            json.dumps(sd)
        )

    sub_queue = Queue()
    assert entity_extraction(submission_task, sub_queue) == 1
    assert sub_queue.qsize() == 1

    tenant, submission = sub_queue.get_nowait()
    assert tenant == TENANT
    assert submission[SUBMISSION_EXTRACTION_FLAG] is True
    assert ENTITY_EXTRACTION_ENRICHMENT in submission[SUBMISSION_PAYLOAD_FIELD]
    assert ENTITY_EXTRACTION_ERRORS not in submission[SUBMISSION_PAYLOAD_FIELD]
    assert SUBMISSION_ENTITIES_FIELD in submission
    assert len(submission[SUBMISSION_ENTITIES_FIELD]) == 3

    # included in cache
    assert cache_has_object(submission['id'], tenant) == CacheType.NORMAL
    assert cache_has_object('missing_id', tenant) == CacheType.NONE


def test__manager_entity_extraction__conform_no_mapping(redis_fn_scope):
    sub_queue = Queue()
    task = Task(
        id=str(uuid.uuid4()),
        data=WRONG_SUBMISSION_PAYLOAD,
        type=f'_{SUBMISSION_CHANNEL}',
        tenant=TENANT,
    )

    assert entity_extraction(task, sub_queue) == 1
    assert sub_queue.qsize() == 1

    tenant, submission = sub_queue.get_nowait()
    assert tenant is TENANT
    assert submission[SUBMISSION_EXTRACTION_FLAG] is True
    assert ENTITY_EXTRACTION_ENRICHMENT not in submission[SUBMISSION_PAYLOAD_FIELD]
    assert ENTITY_EXTRACTION_ERRORS not in submission[SUBMISSION_PAYLOAD_FIELD]
    assert SUBMISSION_ENTITIES_FIELD in submission
    assert len(submission[SUBMISSION_ENTITIES_FIELD]) == 0

    # included in cache
    assert cache_has_object(submission['id'], tenant) == CacheType.NORMAL


def test__manager_entity_extraction__unknown_mapping(redis_fn_scope):
    sub_queue = Queue()
    task = Task(
        id=str(uuid.uuid4()),
        data=WRONG_SUBMISSION_MAPPING,
        type=f'_{SUBMISSION_CHANNEL}',
        tenant=TENANT,
    )

    assert entity_extraction(task, sub_queue) == 0
    assert sub_queue.qsize() == 1

    tenant, submission = sub_queue.get_nowait()
    assert tenant == TENANT
    assert submission[SUBMISSION_EXTRACTION_FLAG] is False
    assert ENTITY_EXTRACTION_ENRICHMENT not in submission[SUBMISSION_PAYLOAD_FIELD]
    assert ENTITY_EXTRACTION_ERRORS in submission[SUBMISSION_PAYLOAD_FIELD]
    assert SUBMISSION_ENTITIES_FIELD not in submission

    # included in cache
    assert cache_has_object(submission['id'], tenant) is CacheType.NORMAL


def test__manager_push_submissions_to_kernel(redis_fn_scope):

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

    prepared = get_prepared(sub_queue)
    assert sub_queue.qsize() == 0
    assert dict(prepared) == {TENANT: [_obj_t1], TENANT_2: [_obj_t1, _obj_t2]}

    with mock.patch('extractor.utils.kernel_data_request') as _mock_fn:
        _mock_fn.side_effect = _mock_fn_side_effect
        # emulate worker
        for realm, objs in prepared.items():
            push_to_kernel(realm, objs, sub_queue)

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

    assert count_quarantined() == 1
    q = Queue()
    get_failed_objects(q)
    assert q.qsize() == 0


def test__manager_workflow(redis_fn_scope, submission_task):
    # test extraction with missing schema definition in schema decorator
    redis = redis_fn_scope
    assert len(SCHEMA_DECORATORS) == 3
    remove_definitions = copy.deepcopy(SCHEMA_DECORATORS)
    for sd in remove_definitions:
        sd.pop(ARTEFACT_NAMES.schema_definition)
        redis.set(
            build_redis_key(ARTEFACT_NAMES.schemadecorators, TENANT, sd['id']),
            json.dumps(sd)
        )

    sub_queue = Queue()
    assert entity_extraction(submission_task, sub_queue) == 1
    assert sub_queue.qsize() == 1

    prepared = get_prepared(sub_queue)
    assert sub_queue.qsize() == 0
    assert TENANT in dict(prepared)

    with mock.patch('extractor.utils.kernel_data_request') as _mock_fn:
        # emulate worker
        for realm, objs in prepared.items():
            push_to_kernel(realm, objs, sub_queue)

        _mock_fn.assert_has_calls([
            mock.call(
                url='submissions.json',
                method='patch',
                data=prepared[TENANT],
                realm=TENANT,
            ),
        ])

    # no errors/quarantine
    assert count_quarantined() == 0
    q = Queue()
    get_failed_objects(q)
    assert q.qsize() == 0
    assert sub_queue.qsize() == 0


def test__manager_workflow__error(redis_fn_scope, submission_task):
    redis = redis_fn_scope
    # test extraction with missing schema definition in schema decorator
    assert len(SCHEMA_DECORATORS) == 3
    remove_definitions = copy.deepcopy(SCHEMA_DECORATORS)
    for sd in remove_definitions:
        sd.pop(ARTEFACT_NAMES.schema_definition)
        redis.set(
            build_redis_key(ARTEFACT_NAMES.schemadecorators, TENANT, sd['id']),
            json.dumps(sd)
        )

    sub_queue = Queue()
    assert entity_extraction(submission_task, sub_queue) == 1
    assert sub_queue.qsize() == 1

    prepared = get_prepared(sub_queue)
    assert sub_queue.qsize() == 0
    assert TENANT in dict(prepared)

    with mock.patch('extractor.utils.kernel_data_request') as _mock_fn:
        _mock_fn.side_effect = HTTPError(response=mock.Mock(status_code=500))
        # emulate worker
        for realm, objs in prepared.items():
            push_to_kernel(realm, objs, sub_queue)

        _mock_fn.assert_has_calls([
            mock.call(
                url='submissions.json',
                method='patch',
                data=prepared[TENANT],
                realm=TENANT,
            ),
        ])

    assert count_quarantined() == 0
    q = Queue()
    get_failed_objects(q)
    assert q.qsize() == 1
    assert sub_queue.qsize() == 1


def test__manager_workflow__quarantine(redis_fn_scope, submission_task):
    redis = redis_fn_scope
    # test extraction with missing schema definition in schema decorator
    assert len(SCHEMA_DECORATORS) == 3
    remove_definitions = copy.deepcopy(SCHEMA_DECORATORS)
    for sd in remove_definitions:
        sd.pop(ARTEFACT_NAMES.schema_definition)
        redis.set(
            build_redis_key(ARTEFACT_NAMES.schemadecorators, TENANT, sd['id']),
            json.dumps(sd)
        )

    sub_queue = Queue()
    assert entity_extraction(submission_task, sub_queue) == 1
    assert sub_queue.qsize() == 1

    prepared = get_prepared(sub_queue)
    assert sub_queue.qsize() == 0
    assert TENANT in dict(prepared)

    with mock.patch('extractor.utils.kernel_data_request') as _mock_fn:
        _mock_fn.side_effect = HTTPError(response=mock.Mock(status_code=400))
        # emulate worker
        for realm, objs in prepared.items():
            push_to_kernel(realm, objs, sub_queue)

        _mock_fn.assert_has_calls([
            mock.call(
                url='submissions.json',
                method='patch',
                data=prepared[TENANT],
                realm=TENANT,
            ),
        ])

    # no errors but quarantine
    assert count_quarantined() == 1
    q = Queue()
    get_failed_objects(q)
    assert q.qsize() == 0
    assert sub_queue.qsize() == 0
