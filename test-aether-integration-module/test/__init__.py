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

import os
from time import sleep

import pytest
import requests

from aether.client import KernelClient
import aether.saladbar.wizard as wizard


from .consumer import get_consumer, read


KERNEL_URL = os.environ['KERNEL_URL']

kernel_credentials = {
    "username": os.environ['KERNEL_ADMIN_USERNAME'],
    "password": os.environ['KERNEL_ADMIN_PASSWORD'],
}

kernel_retry = 15
kernel_retry_time = 1

SEED_ENTITIES = int(os.environ['GENERATED_ENTITY_COUNT'])
SEED_TYPE = "Person"


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
    try:
        wizard.test_setup()
        return True
    except Exception as err:
        raise(err)
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
def producer_status():
    max_retry = 10
    url = os.environ['PRODUCER_STATUS_URL']
    for x in range(max_retry):
        try:
            status = requests.get(url).json()
            kafka = status.get('kafka_container_accessible')
            if not kafka:
                raise ValueError('Kafka not connected yet')
            person = status.get('topics', {}).get(SEED_TYPE, {})
            ok_count = person.get('last_changeset_status', {}).get('succeeded')
            if ok_count:
                sleep(5)
                return ok_count
            else:
                sleep(1)
        except Exception as err:
            print(err)
            sleep(1)


@pytest.fixture(scope="function")
def existing_entities(aether_client, existing_projectschemas):
    entities = {}
    for ps in existing_projectschemas:
        name = ps.get("name")
        endpoint = aether_client.Entity.get(name, strict=False)
        entities[name] = [i for i in endpoint]
    return entities


@pytest.fixture(scope="module")
def generate_entities(aether_client, existing_schemas, existing_projectschemas):
    entities = []
    manager = None
    from aether.mocker import MockingManager, MockFn, Generic
    person = "org.eha.demo.Person"
    location = "org.eha.demo.GeoLocation"
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
        print(err)
    finally:
        try:
            if manager:
                manager.kill()
        except Exception as oos:
            raise(oos)
    return entities


@pytest.fixture(scope="function")
def read_people():
    consumer = get_consumer(SEED_TYPE)
    messages = read(consumer, start="FIRST", verbose=False, timeout_ms=500)
    consumer.close()  # leaving consumers open can slow down zookeeper, try to stay tidy
    return messages
