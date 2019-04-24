#!/usr/bin/env python

# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
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

from confluent_kafka import KafkaException
from datetime import datetime
import pytest
import requests
import threading
from time import sleep
from typing import (
    List
)
import uuid

from producer.logger import LOG
from producer.redis_producer import RedisProducer
from producer.replay_manager import count_entities, get_all_db_updates
from producer.resource import (
    Event,
    Resource,
    ResourceHelper
)
from producer.timeout import timeout as Timeout

# Test Assets
from . import (
    MockCallable,
    MockProducerManager,
    USER,
    PW
)
from . import *  # noqa  # get fixtures


@pytest.mark.integration
def test_manager_http_endpoint_service(ProducerManagerSettings):
    man = MockProducerManager(ProducerManagerSettings)
    with Timeout(5):
        try:
            auth = requests.auth.HTTPBasicAuth(USER, PW)
            man.serve()
            man.add_endpoints()
            sleep(1)
            url = 'http://localhost:%s' % man.settings.get('server_port')
            r = requests.head(f'{url}/healthcheck')
            assert(r.status_code == 200)
            protected_endpoints = ['status', 'topics']
            for e in protected_endpoints:
                r = requests.head(f'{url}/{e}')
                assert(r.status_code == 401)
            for e in protected_endpoints:
                r = requests.head(f'{url}/{e}', auth=auth)
                assert(r.status_code == 200)
        except TimeoutError:
            assert(False), 'Endpoint check timed out'
        finally:
            man.http.stop()
            man.http.close()
            man.worker_pool.kill()


@pytest.mark.integration
def test_initialize_database_get_set(OffsetDB):
    with pytest.raises(ValueError):
        OffsetDB.get('some_missing')
    value = str(uuid.uuid4())
    OffsetDB.set('fake_entry', value)
    assert(OffsetDB.get('fake_entry').value == value)


# Resource Helper Tests

R_TYPE = 'test_resource'
R_BODY = {
    'id': '_an_id',
    'content': 'arbitrary'
}


@pytest.mark.integration
def test_resource__io(get_resource_helper):
    RH: ResourceHelper = get_resource_helper
    # write resource
    _id = R_BODY['id']
    RH.add(_id, R_BODY, R_TYPE)
    # read
    res = RH.get(_id, R_TYPE)
    assert(isinstance(res, Resource))
    assert(res.data['content'] == R_BODY['content'])
    assert(res.type == R_TYPE)
    # delete
    RH.remove(_id, R_TYPE)
    with pytest.raises(ValueError):
        RH.get(_id, R_TYPE)


@pytest.mark.integration
def test_resource__event_listener(get_resource_helper):
    RH: ResourceHelper = get_resource_helper
    # register listener
    # callback
    callable: MockCallable = MockCallable()  # results go here
    listener_pattern = f'{R_TYPE}:*'
    RH.subscribe(callable.add_event, listener_pattern)
    # write
    _id = R_BODY['id']
    RH.add(_id, R_BODY, R_TYPE)
    # update
    new_body = dict(R_BODY)
    new_body['content'] = 'an arbitrary change'
    RH.add(_id, new_body, R_TYPE)
    # delete
    RH.remove(_id, R_TYPE)
    # wait a second
    # assert order of events
    sleep(.1)
    events: List[Event] = callable.events
    expected_order = ['set', 'set', 'del']
    evt_order = [e.event_type for e in events]
    for ev1, ev2 in zip(expected_order, evt_order):
        assert(ev1 == ev2)
    RH.unsubscribe(listener_pattern)


@pytest.mark.integration
def test_resource__iteration(get_resource_helper):
    RH: ResourceHelper = get_resource_helper
    _ids = ['a', 'b', 'c']
    for _id in _ids:
        body = dict(R_BODY)
        body['id'] = _id
        RH.add(_id, body, R_TYPE)
    expected_ids = _ids[:]
    res_gen = RH.list(R_TYPE)
    for res in res_gen:
        expected_ids.remove(res.id)
    assert(len(expected_ids) == 0)
    expected_ids = _ids[:]
    res_gen = RH.list_ids(R_TYPE)
    for _id in res_gen:
        expected_ids.remove(_id)
    assert(len(expected_ids) == 0)


# @pytest.mark.integration
# def test_kafka__basic_io(simple_consumer, simple_producer):
#     size = 10
#     topic = 'kafka-basic-io-test'
#     p = simple_producer
#     c = simple_consumer
#     for x in range(size):
#         p.poll(0)
#         p.produce(topic, str(x).encode('utf-8'))
#     p.flush()
#     c.subscribe([topic])
#     remaining = size
#     try:
#         with Timeout(15):
#             while remaining:
#                 messages = c.consume(size, timeout=1)
#                 for msg in messages:
#                     remaining -= 1
#                 if not messages:
#                     sleep(.1)
#             assert(True)
#     except TimeoutError:
#         assert(False), \
#             'basic kafka io timed out, check kafka test configuration'

@pytest.mark.integration
def test_production_options_from_redis(
    redis_fixture_schemas,
    get_redis_producer
):
    redis_producer: RedisProducer = get_redis_producer
    schemas, decorators = redis_fixture_schemas
    for _id in decorators:
        decorator = decorators[_id]
        topic, serialize_mode, schema = redis_producer.get_production_options(_id)
        assert(topic == f'{decorator.tenant}__{decorator.topic_name}')
        assert(serialize_mode == decorator.serialize_mode)
        schema_id = decorator.schema_id
        assert(schema.id == schema_id)


@pytest.mark.integration
def test_read_entities_list_from_redis(
    redis_fixture_schemas,
    generate_redis_entities,
    get_redis_producer
):
    redis_producer: RedisProducer = get_redis_producer
    schemas, decorators = redis_fixture_schemas
    # create some entities in redis, as the DB service / direct-inject would
    tenant = 'test'
    loads = [10, 100, 1000]  # one load for each decorator
    for key, load in zip(decorators.keys(), loads):
        # make some entites for each decorator
        generate_redis_entities(load, tenant, decorators[key].id)
    # unfiltered
    expect_all_ids = redis_producer.get_entity_keys()
    #   check ordering
    t0, t1 = expect_all_ids[0:2]
    assert(t0 < t1), f'{t1} should have a later offset than {t0}'
    #   check correct unique decorator ids
    unique_decorators = redis_producer.get_unique_decorator_ids(expect_all_ids)
    assert(all([i in unique_decorators for i in decorators.keys()]))
    #   check correct number
    assert(len(expect_all_ids) == sum(loads))
    ignore = decorators[list(decorators.keys())[0]].id
    # filtered
    expect_ids_12 = redis_producer.get_entity_keys(ignored_decorators=[ignore])
    #   check correct number
    assert(len(expect_ids_12) == sum(loads[1:]))
    g = redis_producer.get_entity_generator(expect_all_ids)
    force_fetch_all = sum([1 for i in g])
    assert(force_fetch_all == sum(loads))


'''
@pytest.mark.integration
@pytest.mark.parametrize('decorator_name,count,msg_size,fails', [
    # decorator | count | size | fails
    #   # raises ValueError on missing decorator
    ('decorator_id_-1', 1, 32, True),
    #   # raises KafkaException and fails on new topic creation
    ('decorator_id_1', 1, 32, True),
    # ('decorator_id_1', 1000, 512, False),
    # ('decorator_id_1', 1000, 2048, False),
    # ('decorator_id_1', 1000, 4096, False),
    # ('decorator_id_1', 500, 16096, False),
    # ('decorator_id_1', 500, 32096, False),
    # #   # 1MB size works but is generally not advisable in kafka land
    # ('decorator_id_1', 10, 1_032_096, False),
    #   # raises KafkaException and fails on new topic creation
    ('decorator_id_2', 1, 32, True),
    # ('decorator_id_2', 1000, 128, False),
    # ('decorator_id_2', 1000, 2048, False),
    # ('decorator_id_2', 1000, 4096, False),
    # ('decorator_id_2', 500, 16096, False),
    # ('decorator_id_2', 500, 32096, False),
    ('decorator_id_3', 1, 32, True),
])
def test_produce__topic_variations(
    get_redis_producer,
    redis_fixture_schemas,
    generate_redis_entities,
    decorator_name,
    count,
    msg_size,
    fails
):
    redis_producer: RedisProducer = get_redis_producer
    schemas, decorators = redis_fixture_schemas
    tenant = 'test'
    generate_redis_entities(count, tenant, decorator_name, msg_size)
    entity_keys = redis_producer.get_entity_keys()
    try:
        redis_producer.produce_from_pick_list(entity_keys)
        if not fails:
            assert(True)
    except (KafkaException, ValueError):
        if not fails:
            assert(False)
        else:
            assert(True)


@pytest.mark.integration
def test_produce__multiple_simultaneous(
    get_redis_producer,
    redis_fixture_schemas,
    generate_redis_entities,
):
    # simulate normal operation by having multiple topics with interspersed offsets
    # and varying size
    redis_producer: RedisProducer = get_redis_producer
    schemas, decorators = redis_fixture_schemas
    to_generate = [
        (1000, 'test', 'decorator_id_1', 1048),
        (10000, 'test', 'decorator_id_1', 128),
        (1000, 'test', 'decorator_id_2', 2096),
        (10000, 'test', 'decorator_id_2', 128),
        (1000, 'test', 'decorator_id_3', 128),
        (10000, 'test', 'decorator_id_3', 2096)
    ]
    size = sum([i[0] for i in to_generate])
    threads = [
        threading.Thread(target=generate_redis_entities, args=args)
        for args in to_generate
    ]
    LOG.debug(f'generating {size} entities')
    for t in threads:
        t.start()
    for i in threads:
        t.join()
    LOG.debug('producing -> kafka')
    entity_keys = redis_producer.get_entity_keys()
    start = datetime.now()
    redis_producer.produce_from_pick_list(entity_keys)
    end = datetime.now()
    run_time = (end - start).total_seconds()
    LOG.info(f'produced {size} entities in {run_time}s @ {size/run_time} m/s')

    assert(True)
'''


@pytest.mark.integration
def test_kernel_entities_count(get_kernel_fixtures, generate_kernel_entities):
    _, _, sds = get_kernel_fixtures
    count = 10
    generate_kernel_entities(count, value_size=2000)
    _ids = [i.id for i in sds]
    assert(count == count_entities(_ids))


@pytest.mark.integration
def test_kernel_entities_get():
    # count existing from previous test
    # count = 10
    entities = get_all_db_updates()
    for e in entities:
        LOG.debug(e)
