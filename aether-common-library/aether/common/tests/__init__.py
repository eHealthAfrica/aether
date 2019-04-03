# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the "License");
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

import json
import sys

from importlib import reload, import_module

from django.conf import settings
from django.test import TestCase
from django.urls import clear_url_caches


class UrlsTestCase(TestCase):

    def setUp(self):
        reload(sys.modules[settings.ROOT_URLCONF])
        import_module(settings.ROOT_URLCONF)
        clear_url_caches()

    def tearDown(self):
        clear_url_caches()


class MockResponse:

    def __init__(self, status_code=200, json_data={}):
        self.json_data = json_data
        self.status_code = status_code
        self.content = json.dumps(json_data).encode('utf-8')

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(self.status_code)
