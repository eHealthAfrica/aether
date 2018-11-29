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
def test_initialize_database_get_set(ProducerManagerSettings):
    man = MockProducerManager(ProducerManagerSettings)
    man.init_db()
    assert(Offset.get_offset('some_missing') is None)
    value = str(uuid.uuid4())
    new_offset = Offset.update('fake_entry', value)
    assert(Offset.get_offset('fake_entry').offset_value == value)
