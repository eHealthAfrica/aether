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
    try:
        with Timeout(1):
            OffsetDB.get_offset(osn)
    except TimeoutError:
        pass
    else:
        assert(False), 'Operation should have timed out.'
    for conn in conns:
        OffsetQueue.release('test', conn)


@pytest.mark.integration
def test_offset_prioritization(OffsetQueue, OffsetDB):
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
    try:
        with Timeout(1):
            conn = low_prio.get()
    except TimeoutError:
        pass
    else:
        assert(False), 'Operation should have timed out.'
    with Timeout(1):
        conn = high_prio.get()
        assert(OffsetQueue._test_connection(conn) is True)
    for conn in conns:
        OffsetQueue.release('test', conn)
