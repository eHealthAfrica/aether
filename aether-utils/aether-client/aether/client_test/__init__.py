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

from aether.client_test import fixtures as fix
import os
import pytest
from time import sleep

from aether.client import Client

URL = os.environ['KERNEL_URL']
USER = os.environ['KERNEL_ADMIN_USERNAME']
PW = os.environ['KERNEL_ADMIN_PASSWORD']


@pytest.fixture(scope='session')
def client():
    return Client(URL, USER, PW)


@pytest.fixture(scope='session')
def project(client):
    # You can pass a dictionary directly to the client
    obj = dict(fix.project_template)
    obj['name'] = fix.project_name
    project = client.projects.create(data=obj)
    return project


@pytest.fixture(scope='session')
def schemas(client):
    schemas = []
    for definition in fix.schema_definitions:
        # You can use a dictionary to populate a model as **kwargs
        for x in range(100):
            try:
                tpl = dict(fix.schema_template)
                tpl['name'] = definition['name']
                tpl['definition'] = definition
                Schema = client.get_model('Schema')
                schema = Schema(**tpl)
                schemas.append(client.schemas.create(data=schema))
                break
            except Exception as err:
                print(x, err)
                sleep(.1)

    return schemas


@pytest.fixture(scope='session')
def projectschemas(client, project, schemas):
    ps_objects = []
    for schema in schemas:
        # You can also use the model constructor
        for x in range(100):
            try:
                PS = client.get_model('ProjectSchema')
                ps = PS(
                    name=schema.name,
                    revision='1',
                    project=project.id,
                    schema=schema.id
                )
                ps_objects.append(client.projectschemas.create(data=ps))
                break
            except Exception as err:
                print(x, err)
                sleep(.1)
    return ps_objects


@pytest.fixture(scope='session')
def mapping(client, project, projectschemas):
    obj = dict(fix.mapping_template)
    _map = dict(fix.mapping_definition)
    _map['entities'] = {ps.name: ps.id for ps in projectschemas}
    obj['project'] = project['id']
    obj['definition'] = _map
    for x in range(100):
        try:
            result = client.mappings.create(data=obj)
            break
        except Exception as err:
            print(x, err)
            sleep(.1)
    return result
