# Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
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

from aether.client import fixtures as fix
import os
import pytest
import random
import string
from uuid import uuid4

from aether.client import Client

URL = os.environ['KERNEL_URL']
USER = os.environ['KERNEL_USERNAME']
PW = os.environ['KERNEL_PASSWORD']


def simple_entity(value_size=10):
    return {
        'id': str(uuid4()),
        'value': ''.join(
            random.choices(
                string.ascii_uppercase + string.digits, k=value_size)
        )
    }


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
        tpl = dict(fix.schema_template)
        tpl['name'] = definition['name']
        tpl['definition'] = definition
        Schema = client.get_model('Schema')
        schema = Schema(**tpl)
        schemas.append(client.schemas.create(data=schema))

    return schemas


@pytest.fixture(scope='session')
def schemadecorators(client, project, schemas):
    sd_objects = []
    for schema in schemas:
        # You can also use the model constructor
        SD = client.get_model('SchemaDecorator')
        sd = SD(
            name=schema.name,
            revision='1',
            project=project.id,
            schema=schema.id
        )
        sd_objects.append(client.schemadecorators.create(data=sd))
    return sd_objects


@pytest.fixture(scope='session')
def single_entities(client, schemadecorators):
    sd = [i for i in schemadecorators if i.name == 'Simple'][0]
    Entity = client.get_model('Entity')

    def _gen(count):
        entities = []
        for i in range(count):
            e = Entity(**{
                'schemadecorator': sd['id'],
                'status': 'Publishable',
                'payload': simple_entity()
            })
            entities.append(client.entities.create(data=e))
        return entities
    yield _gen


@pytest.fixture(scope='session')
def bulk_entities(client, schemadecorators):
    sd = [i for i in schemadecorators if i.name == 'Simple'][0]

    def _gen(count):
        entities = []
        for i in range(count):
            e = {
                'schemadecorator': sd['id'],
                'status': 'Publishable',
                'payload': simple_entity()
            }
            entities.append(e)
        return client.entities.create(data=entities)
    yield _gen


@pytest.fixture(scope='session')
def mappingset(client, project):
    MappingSet = client.get_model('MappingSet')
    mapping_set = MappingSet(name='test_mapping_set', project=project.id)
    return client.mappingsets.create(data=mapping_set)


@pytest.fixture(scope='session')
def mapping(client, project, schemadecorators, mappingset):
    obj = dict(fix.mapping_template)
    _map = dict(fix.mapping_definition)
    _map['entities'] = {sd.name: sd.id for sd in schemadecorators}
    obj['project'] = project['id']
    obj['mappingset'] = mappingset.id
    obj['definition'] = _map
    result = client.mappings.create(data=obj)
    return result
