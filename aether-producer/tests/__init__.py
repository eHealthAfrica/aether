#!/usr/bin/env python

# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
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

from datetime import datetime
import pytest
import os
import random
import string
from time import sleep
from typing import (
    Dict,
    Iterable,
    List,
    Tuple
)
from uuid import uuid4

from aether.client import Client
from confluent_kafka import Producer, Consumer
from producer import (
    ProducerManager,
    OFFSET_MANAGER
)

from producer.db import Decorator, Entity
from producer.redis_producer import RedisProducer
from producer.resource import Event, ResourceHelper, RESOURCE_HELPER
from producer.settings import Settings
from producer.logger import LOG


USER = os.environ['PRODUCER_ADMIN_USER']
PW = os.environ['PRODUCER_ADMIN_PW']


def entity_generator(
    count: int,
    tenant: str,
    decorator_id: str,
    value_size: int = 32
) -> Iterable[Entity]:

    for i in range(count):
        _id = str(uuid4())
        yield(Entity(
            id=_id,
            offset=str(datetime.now().isoformat()),
            tenant=tenant,
            decorator_id=decorator_id,
            payload={
                'id': _id,
                'value': ''.join(
                    random.choices(
                        string.ascii_uppercase + string.digits, k=value_size)
                )
            }
        ))


PROJECT = {
    "revision": "1",
    "name": 'TestProject'
}

SCHEMAS = {
    'simple_schema_id': {
        'doc': 'A Simple Schema',
        'name': 'Test',
        'type': 'record',
        'fields': [
            {
                'doc': 'ID',
                'name': 'id',
                'type': 'string',
                'jsonldPredicate': '@id'
            },
            {
                'doc': 'The Value',
                'name': 'value',
                'type': 'string'
            }
        ],
        'namespace': 'eha.aether.producer.test'
    }
}

SCHEMA_DECORATORS = {
    'decorator_id_1': Decorator(**{
        'id': 'decorator_id_1',
        'tenant': 'test',
        'serialize_mode': 'single',
        'schema_id': 'simple_schema_id',
        'topic_name': 'd1'
    }),
    'decorator_id_2': Decorator(**{
        'id': 'decorator_id_2',
        'tenant': 'test2',
        'serialize_mode': 'multi',
        'schema_id': 'simple_schema_id',
        'topic_name': 'd2'
    }),
    'decorator_id_3': Decorator(**{
        'id': 'decorator_id_3',
        'tenant': 'test',
        'serialize_mode': 'single',
        'schema_id': 'simple_schema_id',
        'topic_name': 'd3'
    })
}


class MockCallable(object):
    events: List[Event] = []

    def add_event(self, evt: Event):
        LOG.debug(f'MockCallable got msg: {evt}')
        self.events.append(evt)


class MockProducerManager(ProducerManager):

    def __init__(self, settings):
        self.admin_name = USER
        self.admin_password = PW
        self.settings = settings
        self.killed = False
        self.kernel = None
        self.kafka = False
        self.topic_managers = {}


class ObjectWithKernel(object):

    def __init__(self, initial_kernel_value=None):
        self.kernel = initial_kernel_value


@pytest.mark.integration
@pytest.fixture(scope='session')
def get_kernel(ProducerManagerSettings) -> Iterable[Client]:
    S = ProducerManagerSettings
    kernel = Client(
        S['kernel_url'],
        S['kernel_username'],
        S['kernel_password'],
    )
    yield kernel


@pytest.mark.integration
@pytest.fixture(scope='session')
def get_kernel_fixtures(get_kernel) -> Iterable[Tuple[Dict, Dict, List[Dict]]]:
    kernel = get_kernel
    project = kernel.projects.create(data=PROJECT)
    schema_id = list(SCHEMAS.keys())[0]
    Schema = kernel.get_model('Schema')
    schema = Schema(**{
        'name': schema_id,
        'type': 'record',
        'revision': '1',
        'definition': SCHEMAS[schema_id]
    })
    schema = kernel.schemas.create(data=schema)
    SD = kernel.get_model('SchemaDecorator')
    sds = []
    for decorator in SCHEMA_DECORATORS.items():
        sd = SD(
            name=schema.name,
            revision='1',
            project=project.id,
            schema=schema.id
        )
        sds.append(kernel.schemadecorators.create(data=sd))
    yield (project, schema, sds)

    # clean-up kernel
    for sd in sds:
        kernel.schemadecorators.delete(id=sd.id)
    kernel.schemas.delete(id=schema.id)
    kernel.projects.delete(id=project.id)


@pytest.mark.integration
@pytest.fixture(scope='session')
def generate_kernel_entities(get_kernel, get_kernel_fixtures):
    kernel = get_kernel
    project, schema, sds = get_kernel_fixtures
    cleanup_keys = []
    sd = sds[0]
    Entity = kernel.get_model('Entity')
    LOG.debug(dir(Entity))

    def make_entity_instances(
        count: int,
        tenant: str = 'default',
        decorator_id: str = 'default',
        value_size: int = 32,
        delay=None
    ):

        LOG.debug(dir(kernel))
        LOG.debug(dir(kernel.entities))
        start = datetime.now()
        entities = []
        for e in entity_generator(count, tenant, decorator_id, value_size):
            entity = {
                'id': e.id,
                'schemadecorator': sd.id,
                'status': 'Publishable',
                'payload': e.payload
            }
            cleanup_keys.append(e.id)
            entities.append(entity)
        try:
            entities = kernel.entities.create(data=entities, many=True)
            LOG.debug(entities)
        except Exception as err:
            LOG.error(err)

        end = datetime.now()
        run_time = (end - start).total_seconds()
        LOG.debug(f'generated {count} entities @ {count / run_time}')

    yield make_entity_instances
    # clean-up kernel
    
    # for _id in cleanup_keys:
    #     try:
    #         kernel.entities.delete(id=_id)
    #     except Exception as err:
    #         LOG.error(err)


@pytest.mark.integration
@pytest.fixture(scope='session')
def get_resource_helper() -> Iterable[ResourceHelper]:
    yield RESOURCE_HELPER
    # cleanup at end of session
    RESOURCE_HELPER.stop()


@pytest.mark.integration
@pytest.fixture(scope='function')
def get_redis_producer(get_resource_helper) -> Iterable[RedisProducer]:
    RH = get_resource_helper
    yield RedisProducer(RH)


@pytest.mark.integration
@pytest.fixture(scope='session')
def ProducerManagerSettings():
    return Settings('/code/tests/conf/producer.json')


@pytest.mark.integration
@pytest.fixture(scope='session')
def OffsetDB():
    return OFFSET_MANAGER


@pytest.mark.integration
@pytest.fixture(scope='session')
def kafka_settings(ProducerManagerSettings):
    kafka_settings = ProducerManagerSettings.get('kafka_settings')
    kafka_settings['bootstrap.servers'] = \
        ProducerManagerSettings.get('kafka_bootstrap_servers')
    return kafka_settings


@pytest.mark.integration
@pytest.fixture(scope='session')
def simple_producer(kafka_settings):
    producer = Producer(**kafka_settings)
    yield producer


@pytest.mark.integration
@pytest.fixture(scope='function')
def simple_consumer(kafka_settings):
    ks = dict(kafka_settings)
    ks['group.id'] = str(uuid4())
    consumer = Consumer(**ks)
    yield consumer
    consumer.close()


@pytest.mark.integration
@pytest.fixture(scope='function')
def redis_fixture_schemas(get_resource_helper):
    RH: ResourceHelper = get_resource_helper
    for _id, schema in SCHEMAS.items():
        RH.add(_id, schema, 'schema')

    for _id, decorator in SCHEMA_DECORATORS.items():
        RH.add(_id, decorator._asdict(), 'decorator')

    yield(SCHEMAS, SCHEMA_DECORATORS)

    for _id, schema in SCHEMAS.items():
        RH.remove(_id, 'schema')

    for _id, decorator in SCHEMA_DECORATORS.items():
        RH.remove(_id, 'decorator')


@pytest.mark.integration
@pytest.fixture(scope='function')
def generate_redis_entities(get_resource_helper):
    RH = get_resource_helper
    cleanup_keys = []

    def make_entity_instances(
        count: int,
        tenant: str,
        decorator_id: str,
        value_size: int = 32,
        delay=None
    ):
        for e in entity_generator(count, tenant, decorator_id, value_size):
            queue_key = f'{e.offset}/{decorator_id}/{e.id}'
            cleanup_keys.append(queue_key)
            RH.add(queue_key, e._asdict(), 'entity')
            if delay:
                sleep(delay)
    yield make_entity_instances
    # cleanup redis
    for key in cleanup_keys:
        RH.remove(key, 'entity')
