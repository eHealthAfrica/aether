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

from aether_producer.producer import db
from aether_producer.producer.db import Offset

from . import *


@pytest.mark.integration
def test_manager_http_endpoint_service(ProducerManagerSettings):
    man = MockProducerManager(ProducerManagerSettings)
    try:
        man.serve()
        man.add_endpoints()
        sleep(1)
        url = 'http://localhost:%s' % self.settings.get('server_port')
        r = requests.head(url + '/status')
        assert(r.status_code == 200)
        r = requests.head(url + '/healthcheck')
        assert(r.status_code == 200)
    finally:
        man.http.stop()
        man.http.close()
        man.worker_pool.kill()


@pytest.mark.integration
def test_initialize_database(ProducerManagerSettings):
    man = MockProducerManager(ProducerManagerSettings)
    man.init_db()
    assert(Offset.get('fake_entry') is None)
    new_offset = Offset.update('fake_entry', 'an_offset_value')
    assert(Offset.get('fake_entry') is 'an_offset_value')
