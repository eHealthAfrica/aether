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

from producer import ProducerManager
from producer.settings import SETTINGS, get_logger


class MockAdminInterface(object):

    def list_topics(self, *args, **kwargs):
        return {}


class MockKernelClient(object):

    def __init__(self):
        self.last_check = None
        self.last_check_error = None

    def mode(self):
        return 'dummy'

    def get_schemas(self):
        return []

    def check_updates(self, modified, schema_name, realm):
        return False

    def count_updates(self, schema_name, realm):
        return 0

    def get_updates(self, modified, schema_name, realm):
        return []


class MockProducerManager(ProducerManager):

    def __init__(self):
        self.admin_name = SETTINGS.get_required('producer_admin_user')
        self.admin_password = SETTINGS.get_required('producer_admin_pw')
        self.killed = False
        self.kernel_client = MockKernelClient()
        self.kafka_status = False
        self.kafka_admin_client = MockAdminInterface()
        self.logger = get_logger('tests')
        self.topic_managers = {}
