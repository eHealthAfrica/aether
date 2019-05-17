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

from .test_fixtures import *  # noqa
import bravado


def test_1_check_fixture_creation(client, project, schemas, schemadecorators, mapping):
    assert(project.id is not None)
    client_schemas = list(client.schemas.paginated('list'))
    assert len(schemas) != 0
    assert(len(client_schemas) == len(schemas))
    client_sd = list(client.schemadecorators.paginated('list'))
    assert(len(client_sd) == len(schemas))
    assert(mapping.id is not None)


def test_2_count_schemas(client, schemas):
    ct = client.schemas.count('list')
    assert(ct == len(schemas))


def test_3_first_schema(client, schemas):
    first = client.schemas.first('list', ordering='modified')
    assert(first.id == schemas[0].id)


def test_4_iterate_schemas(client, schemas):
    _schemas = list(client.schemas.paginated('list'))
    assert(len(_schemas) == len(schemas))


def test_5_make_entites(client, single_entities, bulk_entities):
    single = single_entities(1)
    assert(single is not None)
    many = bulk_entities(10)
    assert(many is not None)
    entities = client.entities.paginated('list')
    i = 0
    for e in entities:
        print(e)
        i += 1
    assert(i == 11)


# After this point, the artifacts we cached are invalidated.
def test_6_update_project(client):
    project = client.projects.first('list')
    new_name = 'a new name'
    project.name = new_name
    client.projects.update(id=project.id, data=project)
    project = client.projects.first('list')
    assert(project.name == new_name)


def test_7_update_project_partial(client, project):
    new_name = 'yet another new name'
    pkg = {'name': new_name}
    client.projects.partial_update(id=project.id, data=pkg)
    retrieved = client.projects.first('list')
    assert(retrieved.name == new_name)


def test_7_delete_project(client, project):
    client.projects.delete(id=project.id)
    projects = list(client.projects.paginated('list'))
    assert(len(projects) == 0)


def test_8_check_bad_url():
    try:
        c = Client("http://localhost/bad-url", "user", "pw")
        c.get('projects')
    except bravado.exception.BravadoConnectionError:
        assert(True)
    else:
        assert(False)


def test_9_check_bad_credentials():
    try:
        c = Client(URL, "user", "pw")
        c.get('projects')
    except bravado.exception.HTTPForbidden:
        assert(True)
    else:
        assert(False)
