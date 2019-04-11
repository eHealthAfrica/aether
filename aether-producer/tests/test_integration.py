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


import requests
from time import sleep
from typing import (
    List
)
import uuid

import pytest

# from producer.logger import LOG
from producer.resource import (
    Event,
    Resource
)

from . import *  # noqa
from . import (
    MockCallable
)


@pytest.mark.integration
def test_manager_http_endpoint_service(ProducerManagerSettings):
    man = MockProducerManager(ProducerManagerSettings)
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
    RH = get_resource_helper
    # write resource
    RH.add(R_BODY, R_TYPE)
    # read
    res = RH.get(R_BODY['id'], R_TYPE)
    assert(isinstance(res, Resource))
    assert(res.data['content'] == R_BODY['content'])
    assert(res.type == R_TYPE)
    # delete
    RH.remove(R_BODY['id'], R_TYPE)
    with pytest.raises(ValueError):
        RH.get(R_BODY['id'], R_TYPE)


@pytest.mark.integration
def test_resource__event_listener(get_resource_helper):
    RH = get_resource_helper
    # register listener
    # callback
    callable: MockCallable = MockCallable()  # results go here
    listener_pattern = f'{R_TYPE}:*'
    RH.subscribe(callable.add_event, listener_pattern)
    # write
    RH.add(R_BODY, R_TYPE)
    # update
    new_body = dict(R_BODY)
    new_body['content'] = 'an arbitrary change'
    RH.add(new_body, R_TYPE)
    # delete
    RH.remove(R_BODY['id'], R_TYPE)
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
    RH = get_resource_helper
    _ids = ['a', 'b', 'c']
    for _id in _ids:
        body = dict(R_BODY)
        body['id'] = _id
        RH.add(body, R_TYPE)
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
