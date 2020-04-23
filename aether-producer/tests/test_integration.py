#!/usr/bin/env python

# Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
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
import uuid

from gevent import Timeout as timeout
from gevent.timeout import Timeout as TimeoutError

from . import *


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
    assert(OffsetDB.get_offset('some_missing') is None)
    value = str(uuid.uuid4())
    OffsetDB.update('fake_entry', value)
    assert(OffsetDB.get_offset('fake_entry') == value)


@pytest.mark.integration
def test_offset_pooling(OffsetQueue, OffsetDB):
    osn, osv = 'pool_offset_test', '10001'
    OffsetDB.update(osn, osv)
    assert(osv == OffsetDB.get_offset(osn))
    assert(OffsetQueue.max_connections is len(OffsetQueue.connection_pool))
    conns = []
    while not OffsetQueue.connection_pool.empty():
        promise = OffsetQueue.request_connection(0, 'test')
        conn = promise.get()
        assert(OffsetQueue._test_connection(conn) is True)
        conns.append(conn)
    # res = None
    # try:
    #     with timeout(.01):
    #         res = OffsetDB.get_offset(osn)
    # except TimeoutError:
    #     pass
    # if res:
    #     assert(False), 'Operation should have timed out.'
    for conn in conns:
        OffsetQueue.release('test', conn)
    assert(OffsetQueue.max_connections is len(OffsetQueue.connection_pool))


@pytest.mark.integration
def test_offset_prioritization(OffsetQueue, OffsetDB):
    assert(OffsetQueue.max_connections is len(OffsetQueue.connection_pool))
    # Grab all connections
    conns = []
    while not OffsetQueue.connection_pool.empty():
        promise = OffsetQueue.request_connection(0, 'test')
        conn = promise.get()
        assert(OffsetQueue._test_connection(conn) is True)
        conns.append(conn)
    low_prio = OffsetQueue.request_connection(1, 'low')
    high_prio = OffsetQueue.request_connection(0, 'high')
    # free a connection
    conn = conns.pop()
    OffsetQueue.release('test', conn)
    conn = None
    try:
        with timeout(.01):
            conn = low_prio.get()
    except TimeoutError:
        low_prio.set(-1)
    if conn:
        assert(False), 'Operation should have timed out.'
    with timeout(1):
        conn = high_prio.get()
        assert(OffsetQueue._test_connection(conn) is True)
    OffsetQueue.release('high', conn)
    assert(OffsetQueue.max_connections is len(OffsetQueue.connection_pool))


@pytest.mark.integration
def test_offset_fifo_timeouts(OffsetQueue, OffsetDB):
    # Grab all connections
    conns = []
    while not OffsetQueue.connection_pool.empty():
        promise = OffsetQueue.request_connection(0, 'test')
        log.debug('Got connection')
        conn = promise.get()
        assert(OffsetQueue._test_connection(conn) is True)
        conns.append(conn)
    assert(len(OffsetQueue.connection_pool) == 0)
    _qs = []
    for x in range(3):
        name = f'num-{x}'
        promise = OffsetQueue.request_connection(1, name)
        _qs.append(tuple([name, promise]))

    for name, promise in _qs:
        try:
            assert(promise.value is None)
            promise.get_nowait()
            raise RuntimeError('Should be Blocked')
        except TimeoutError:
            log.debug(f'{name} timed out')
        finally:
            promise.set(-1)

    for conn in conns:
        OffsetQueue.release('test', conn)
    assert(OffsetQueue.max_connections is len(OffsetQueue.connection_pool))

    # for x in range(3):
    #     name = f'num-{x}'
    #     k = (1, name)
    #     promise = OffsetQueue.request_connection(*k)
    #     _qs.append(tuple([name, promise]))

    # for name, promise in _qs:
    #     try:
    #         with timeout(.01):
    #             assert(promise.value is None)
    #             promise.get()
    #             raise RuntimeError('Should be Blocked')
    #     except TimeoutError:
    #         log.debug(f'{name} timed out')
    #         promise.set(-1)

    _qs = []
    for x in range(100):
        name = f'num-{x}'
        promise = OffsetQueue.request_connection(1, name)
        _qs.append(tuple([name, promise]))

    while True:
        try:
            name, promise = _qs.pop(0)
            for _key, _promise in _qs:
                try:
                    # log.debug(f'requesting {_key} with busy resource')
                    _promise.get_nowait()
                    raise RuntimeError('Should be Blocked')
                except TimeoutError:
                    # don't fail the promise here so we can check the order
                    # promise.set(-1)
                    # log.debug(f'{_key} timed out')
                    pass
            try:
                with timeout(1):
                    log.debug(f'requesting {name} with empty resource')
                    conn = promise.get()
                    assert(OffsetQueue._test_connection(conn) is True)
            except TimeoutError:
                raise RuntimeError('Should have had a connection available')
            OffsetQueue.release(name, conn)
        except IndexError:
            break
