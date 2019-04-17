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

from datetime import datetime
import pytest
import requests
from time import sleep
from typing import (
    List
)
import uuid

from producer.redis_producer import RedisProducer
from producer.resource import (
    Event,
    Resource,
    ResourceHelper
)

# Test Assets
from . import (
    MockCallable,
    MockProducerManager,
    USER,
    PW
)
from . import *  # noqa  # get fixtures
from .timeout import timeout as Timeout  # noqa


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


@pytest.mark.integration
@pytest.mark.parametrize('decorator_name', [
    'decorator_id_1', 'decorator_id_2', 'decorator_id_3'
])
def test_produce__topic_variations(
    redis_fixture_schemas,
    generate_redis_entities,
    decorator_name
):
    schemas, decorators = redis_fixture_schemas
    decorator = decorators[decorator_name]
    print(decorator)
    tenant = 'test'
    generate_redis_entities(10, tenant, decorator.id)
