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
from gevent import sleep

from aether.producer.settings import SETTINGS
from aether.producer.db import Offset

from .timeout import timeout as Timeout
from . import MockProducerManager


def test_manager_http_endpoint_service():
    man = MockProducerManager()
    try:
        SETTINGS.override('MAX_JOB_IDLE_SEC', 1)
        _realm = 'fake_realm'
        auth = requests.auth.HTTPBasicAuth(man.admin_name, man.admin_password)
        man.serve()
        man.add_endpoints()
        sleep(1)

        url = 'http://localhost:%s' % SETTINGS.get('server_port', 9005)

        r = requests.head(f'{url}/health')
        assert (r.status_code == 200), r.text

        r = requests.head(f'{url}/healthcheck')
        assert (r.status_code == 200), r.text

        r = requests.head(f'{url}/check-app')
        assert (r.status_code == 200), r.text

        r = requests.head(f'{url}/kernelcheck')
        assert (r.status_code == 424), r.text
        r = requests.head(f'{url}/check-app/aether-kernel')
        assert (r.status_code == 424), r.text

        r = requests.head(f'{url}/kafkacheck')
        assert (r.status_code == 424), r.text
        r = requests.head(f'{url}/check-app/kafka')
        assert (r.status_code == 424), r.text

        protected_endpoints = ['status', 'topics']
        for e in protected_endpoints:
            r = requests.head(f'{url}/{e}')
            assert (r.status_code == 401), r.text

        for e in protected_endpoints:
            r = requests.head(f'{url}/{e}', auth=auth)
            assert (r.status_code == 200), r.text

        man.realm_managers[_realm] = {}
        man.thread_checkin(_realm)
        sleep(2)
        r = requests.get(f'{url}/health')
        assert (r.status_code == 200)
        r = requests.get(f'{url}/healthcheck')
        assert (r.status_code == 500), r.text
        assert (_realm in r.json().keys())

    finally:
        SETTINGS.clear_overrides()
        man.http.stop()
        man.http.close()
        man.worker_pool.kill()


def test_initialize_database_get_set():
    try:
        MockProducerManager().init_db()

        assert (Offset.get_offset('some_missing') is None)
        value = str(uuid.uuid4())
        Offset.update('fake_entry', value)
        assert (Offset.get_offset('fake_entry') == value)
    finally:
        Offset.close_pool()


def test_offset_pooling():
    try:
        MockProducerManager().init_db()
        OffsetQueue = Offset.create_pool()

        osn, osv = 'pool_offset_test', '10001'
        Offset.update(osn, osv)
        assert (osv == Offset.get_offset(osn))
        assert (OffsetQueue.max_connections == len(OffsetQueue.connection_pool))

        conns = []
        while not OffsetQueue.connection_pool.empty():
            promise = OffsetQueue.request_connection(0, 'test')
            conn = promise.get()
            assert (OffsetQueue._test_connection(conn))
            conns.append(conn)

        try:
            with Timeout(1):
                Offset.get_offset(osn)
        except TimeoutError:
            assert (True), 'Operation has timed out.'
        else:
            assert (False), 'Operation should have timed out.'
        finally:
            for conn in conns:
                OffsetQueue.release('test', conn)
    finally:
        Offset.close_pool()


def test_offset_prioritization():
    try:
        MockProducerManager().init_db()
        OffsetQueue = Offset.create_pool()

        # Grab all connections
        conns = []
        while not OffsetQueue.connection_pool.empty():
            promise = OffsetQueue.request_connection(0, 'test')
            conn = promise.get()
            assert (OffsetQueue._test_connection(conn))
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
            assert (True), 'Operation has timed out.'
        else:
            assert (False), 'Operation should have timed out.'

        with Timeout(1):
            conn = high_prio.get()
            assert (OffsetQueue._test_connection(conn))

        for conn in conns:
            OffsetQueue.release('test', conn)
    finally:
        Offset.close_pool()
