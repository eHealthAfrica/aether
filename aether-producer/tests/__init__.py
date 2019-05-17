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

import logging
import pytest

from .timeout import timeout as Timeout  # noqa
from producer import *
Offset = db.Offset

log = logging.getLogger()

USER = os.environ['PRODUCER_ADMIN_USER']
PW = os.environ['PRODUCER_ADMIN_PW']


class MockProducerManager(ProducerManager):

    def __init__(self, settings):
        self.admin_name = USER
        self.admin_password = PW
        self.settings = settings
        self.killed = False
        self.kernel = None
        self.kafka = False
        self.logger = log
        self.topic_managers = {}


class ObjectWithKernel(object):

    def __init__(self, initial_kernel_value=None):
        self.kernel = initial_kernel_value
        self.logger = log


@pytest.mark.integration
@pytest.fixture(scope='session')
def ProducerManagerSettings():
    return Settings('/code/tests/conf/producer.json')


@pytest.mark.integration
@pytest.fixture(scope='session')
def OffsetDB(ProducerManagerSettings):
    man = MockProducerManager(ProducerManagerSettings)
    man.init_db()
    return Offset


@pytest.mark.integration
@pytest.fixture(scope='function')
def OffsetQueue():
    return db.OFFSET_DB
