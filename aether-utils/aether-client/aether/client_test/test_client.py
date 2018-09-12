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

from . import *  # noqa
import requests


def test_1_check_fixture_creation(client, project, schemas, projectschemas, mapping):
    assert(project['id'] is not None)
    client_schemas = list(client.get('schemas'))
    assert len(schemas) != 0
    assert(len(client_schemas) == len(schemas))
    client_ps = list(client.get('projectschemas'))
    assert len(client_ps) != 0
    assert(len(client_ps) == len(schemas))
    assert(mapping['id'] is not None)


def test_2_check_bad_url():
    try:
        c = Client("http://localhost/bad-url", "user", "pw")
        c.get('projects')
    except requests.exceptions.ConnectionError:
        assert(True)
    else:
        assert(False)
