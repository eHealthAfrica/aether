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
# software distributed under the License is distributed on anx
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from aether.client import KernelClient
import pytest
import sys
from time import sleep

KERNEL_URL = "http://kernel-test:9000/v1"

kernel_credentials = {
    "username": "admin-kernel",
    "password": "adminadmin",
}

kernel_retry = 3
kernel_retry_time = 5

SEED_ENTITIES = 10
SEED_TYPE = "Person"

py2 = pytest.mark.skipif(sys.version_info >= (3, 0), reason="Test only required for python2")
py3 = pytest.mark.skipif(sys.version_info <= (3, 0), reason="Test only required for python3")


@pytest.fixture(scope="session")
def aether_client():
    for x in range(kernel_retry):
        try:
            client = KernelClient(KERNEL_URL, **kernel_credentials)
            return client
        except Exception as err:
            sleep(kernel_retry_time)
            print("Couldn't connect to Aether: %s" % (err))
            pass

    raise EnvironmentError("Could not connect to Aether Kernel on url: %s" % KERNEL_URL)


@pytest.fixture(scope="session")
def schema_registration():
    from saladbar import wizard  # we have to import this locally so it only gets into @py2 scopes
    try:
        wizard.test_setup()
        return True
    except Exception as err:
        print("Schema registration failed with: %s" % err)
        return False


@pytest.fixture(scope="module")
def existing_projects(aether_client):
    return [i for i in aether_client.Resource.Project]


@pytest.fixture(scope="module")
def existing_schemas(aether_client):
    return [i for i in aether_client.Resource.Schema]


@pytest.fixture(scope="module")
def existing_projectschemas(aether_client):
    return [i for i in aether_client.Resource.ProjectSchema]


@pytest.fixture(scope="function")
def existing_entities(aether_client, existing_projectschemas):
    entities = {}
    for ps in existing_projectschemas:
        name = ps.get("name")
        endpoint = aether_client.Entity.get(name)
        entities[name] = [i for i in endpoint]
    return entities


@pytest.fixture(scope="module")
def generate_entities(aether_client, existing_schemas, existing_projectschemas):
    entities = []
    manager = None
    from aether.mocker import MockingManager, MockFn, Generic
    person = "http://demo.eha.org/Person"
    location = "http://demo.eha.org/GeoLocation"
    try:
        manager = MockingManager(kernel_url=KERNEL_URL)
        manager.types[location].override_property(
            "latitude", MockFn(Generic.geo_lat))
        manager.types[location].override_property(
            "longitude", MockFn(Generic.geo_lng))
        for x in range(SEED_ENTITIES):
            entity = manager.register(person)
            entities.append(entity)
    except Exception as err:
        raise(err)
    finally:
        try:
            if manager:
                manager.kill()
        except Exception as oos:
            raise(oos)
    return entities


@pytest.fixture(scope="function")
def read_people():
    from .consumer import get_consumer, read
    consumer = get_consumer(SEED_TYPE)
    messages = read(consumer, start="FIRST", verbose=True, timeout_ms=500)
    consumer.close()  # leaving consumers open can slow down zookeeper, try to stay tidy
    return messages
