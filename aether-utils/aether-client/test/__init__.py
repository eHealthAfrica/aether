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

from test import fixtures as fix
import os
import pytest

from aether.client import Client

URL = os.environ['KERNEL_URL']
USER = os.environ['KERNEL_ADMIN_USERNAME']
PW = os.environ['KERNEL_ADMIN_PASSWORD']


@pytest.fixture(scope='session')
def client():
    return Client(URL, USER, PW)


@pytest.fixture(scope='session')
def project(client):
    obj = dict(fix.project_template)
    obj['name'] = fix.project_name
    result = client.create('projects', obj)
    return result


@pytest.fixture(scope='session')
def schemas(client, project):
    schemas = []
    for definition in fix.schema_definitions:
        obj = dict(fix.schema_template)
        obj['name'] = definition['name']
        obj['definition'] = definition
        schemas.append(client.create('schemas', obj))
    return schemas


@pytest.fixture(scope='session')
def project_schemas(client, project, schemas):
    ps_objects = []
    for schema in schemas:
        obj = dict(fix.project_schema_template)
        obj['name'] = schema['name']
        obj['project'] = project['id']
        obj['schema'] = schema['id']
        ps_objects.append(client.create('projectschemas', obj))
    return ps_objects
