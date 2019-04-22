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

from confluent_kafka import Producer
from datetime import datetime
import io
import json
import spavro
from spavro.datafile import (
    DataFileReader,
    DataFileWriter
)
from spavro.io import (
    DatumReader,
    DatumWriter,
    validate
)
from time import sleep
from typing import (
    Dict,
    Iterator,
    List,
    Set,
    Tuple,
    Union
)
import sys

from producer.db import (
    Entity,
    Decorator,
    Schema
)
from producer.logger import LOG
from producer.resource import (
    ResourceHelper,
    Resource
)
from producer.settings import PRODUCER_CONFIG
from producer.timeout import timeout as Timeout


class RedisProducer(object):

    # muted resource_ids
    ignored_decorator_ids: Dict[str, str]
    # packages sent to kafka but not acknowledged
    inflight: Set[str]
    # KafkaProducer
    producer: Producer
    # Redis Handler
    resoure_helper: ResourceHelper

    @classmethod
    def get_entity_key(cls, e: Entity) -> str:
        return f'{e.offset}/{e.decorator_id}/{e.id}'

    @classmethod
    def get_entity_key_parts(cls, key: str) -> List[str]:
        return key.split('/')  # offset, decorator_id, entity_id

    def __init__(self, resoure_helper: ResourceHelper):
        self.resoure_helper = resoure_helper
        self.ignored_decorator_ids = {}
        self.inflight = set()
        kafka_settings = PRODUCER_CONFIG.get('kafka_settings')
        # apply setting from root config to be able to use env variables
        kafka_settings["bootstrap.servers"] = PRODUCER_CONFIG.get(
            "kafka_url")
        self.producer = Producer(**kafka_settings)

    ###
    # Production Control
    ###

    #   # Stop a type (decorator_id)
    def ignore_entity_type(self, decorator_id: str) -> None:
        self.ignored_decorator_ids[decorator_id] = datetime.now().isoformat()

    #   # Resume a type (decorator_id)
    def unignore_entity_type(self, decorator_id: str) -> None:
        del self.ignored_decorator_ids[decorator_id]

    #   # Callback on Kafka action
    def kafka_callback(self, err=None, msg=None, _=None, **kwargs):
        if err:
            LOG.error('ERROR %s', [err, msg, kwargs])
        with io.BytesIO() as obj:
            obj.write(msg.value())
            reader = DataFileReader(obj, DatumReader())
            for message in reader:
                _id = message.get("id")
                if err:
                    LOG.debug(
                        f'NO-SAVE: {_id}'
                        f' | err {err.name()}'
                    )
                    try:
                        self.acknowledge_failure(_id)
                    except KeyError:
                        pass
                else:
                    LOG.debug(f'SAVE: {_id}')
                    try:
                        self.acknowledge_success(_id)
                    except KeyError:
                        pass

    #   # Success
    def acknowledge_success(self, _id):
        # remove entity from redis

        # remove _id from inflight
        self.inflight.remove(_id)

    #   # Failure
    def acknowledge_failure(self, _id):
        self.inflight.remove(_id)

    #   # Wait for acknowledgement of all messages
    def wait_for_kafka(self, timeout=30):
        LOG.debug('Waiting for kafka acknowledgement.')
        with Timeout(timeout):
            try:
                while len(self.inflight) > 0:
                    LOG.debug(f'waiting for confirmation of '
                              f'{len(self.inflight)} messages')
                    sleep(.25)
            except TimeoutError:
                LOG.critical(f'Inflight timeout. After {timeout} seconds '
                             f'{len(self.inflight)} messages unaccounted for.')
                LOG.critical(f'This is Fatal. Check Kafka broker settings.')
                sys.exit(1)
        LOG.debug('All messages acknowledged.')
    ###
    # Handle Entities from Redis
    ###

    def get_entity_keys(
        self,
        ignored_decorators: Union[List[str], None] = None,
        limit: int = 10_000
    ) -> List[str]:

        # Reading / sorting 100k entities takes on the order of 1.8s
        valid_keys = []
        key_generator = self.resoure_helper.list_ids('entity')
        if ignored_decorators:
            for key in key_generator:
                _, decorator_id, _ = RedisProducer.get_entity_key_parts(key)
                if decorator_id not in ignored_decorators:
                    valid_keys.append(key)
        else:
            valid_keys = list(key_generator)
        valid_keys.sort()
        return valid_keys[:limit]

    def get_entity_generator(
        self,
        entity_keys: List[str]
    ) -> Iterator[Entity]:

        # entity_keys are sorted by offset -> decorator_id -> entity_id
        for key in entity_keys:
            r: Resource = self.resoure_helper.get(key, 'entity')
            yield Entity(**r.data)

    def get_unique_decorator_ids(self, entity_keys: List[str]) -> List[str]:
        unique_keys = set()
        for key in entity_keys:
            _, decorator_id, _ = RedisProducer.get_entity_key_parts(key)
            unique_keys.add(decorator_id)
        return list(unique_keys)

    ###
    # Send Entities to Kafka
    ###

    def get_production_options(
        self,
        decorator_id: str
    ) -> Tuple[str, str, Schema]:  # topic, serialize_mode, schema

        # get decorator by id & cast from Resource -> Decorator
        d: Decorator = Decorator(
            **self.resoure_helper.get(
                decorator_id,
                'decorator').data
        )
        schema_resource: Resource = self.resoure_helper.get(
            d.schema_id,
            'schema'
        )
        schema: Schema = Schema(
            id=d.schema_id,
            tenant=d.tenant,
            schema=schema_resource.data
        )
        topic = f'{d.tenant}__{d.topic_name}'
        serialize_mode = d.serialize_mode
        return topic, serialize_mode, schema

    def produce_from_pick_list(self, entity_keys: List[str]):
        # we can limit production round size by passing entity_keys[:max]

        # the entities keys are primarily offset ordered, but we want to 
        # serialize messages efficiently. This method separates queues 
        # into schema_id based topic before being sent to kafka.
        decorator_info: Dict[str, List[str]] = {}
        entities: Dict[str, List[str]] = {}
        for key in entity_keys:
            offset, decorator_id, _ = RedisProducer.get_entity_key_parts(key)
            try:
                decorator_info[decorator_id].append(offset)
                entities[decorator_id].append(key)
            except KeyError:
                decorator_info[decorator_id] = [offset]
                entities[decorator_id] = [key]
        for _id, offsets in decorator_info.items():
            start = min(offsets)
            end = max(offsets)
            LOG.debug(
                f'Preparing produce of {_id}'
                f'for offsets: {start} -> {end}'
            )
            entity_iterator = self.get_entity_generator(entities[_id])
            self.produce_topic(_id, entity_iterator)
        self.producer.flush()
        self.wait_for_kafka()

    def produce_topic(
        self,
        decorator_id: str,
        entity_iterator: Iterator[Entity],
        max_bundle_size: int = 250
    ):
        topic: str
        serialize_mode: str  # single / multi
        schema: Schema
        topic, serialize_mode, schema = \
            self.get_production_options(decorator_id)
        avro_schema = spavro.schema.parse(json.dumps(schema.schema))
        try:
            with io.BytesIO() as bytes_writer:
                writer = DataFileWriter(
                    bytes_writer,
                    DatumWriter(),
                    avro_schema,
                    codec='deflate'
                )
                writer.flush()
                trunc_size = len(bytes_writer.getvalue())
                LOG.debug(bytes_writer.getvalue())
                i = 0
                for entity in entity_iterator:
                    i += 1
                    _id = entity.id
                    msg = entity.payload
                    offset = entity.offset
                    if validate(avro_schema, msg):
                        # Message validates against current schema
                        LOG.debug(
                            "ENQUEUE MSG TOPIC: %s, ID: %s, MOD: %s" % (
                                topic,
                                _id,
                                offset
                            ))
                        # register as in flight
                        self.inflight.add(_id)
                        # add to bundle
                        writer.append(msg)
                    else:
                        # Message doesn't have the proper format
                        # for the current schema.
                        LOG.critical(
                            'SCHEMA_MISMATCH:NOT SAVED!'
                            f' TOPIC:{topic}, ID:{_id}'
                        )
                    if serialize_mode == 'single':
                        # commit every round
                        self.produce_bundle(
                            topic,
                            writer,
                            bytes_writer,
                            trunc_size,
                            # only single mode messages can be keyed!
                            key=_id
                        )
                    elif i == max_bundle_size:
                        # or when bundle is big enough
                        self.produce_bundle(
                            topic,
                            writer,
                            bytes_writer,
                            trunc_size
                        )
                        i = 0  # reset counter

                if serialize_mode != 'single' \
                        and i > 0:  # there's something to commit
                    self.produce_bundle(topic, writer, bytes_writer, trunc_size)
        except Exception as err:
            LOG.critical(err)
            raise err

    # enqueue a single bundle for production, but do not flush.
    def produce_bundle(
        self,
        topic: str,
        writer: DataFileWriter,
        bytes_writer: io.BytesIO,
        trunc_size: int,
        key: str = None
    ):
        writer.flush()
        raw_bytes = bytes_writer.getvalue()
        self.producer.produce(
            topic,
            raw_bytes,
            key=key,
            callback=self.kafka_callback
        )
        # bytes_writer.seek(0)
        # bytes_writer.truncate(trunc_size)
        # print(bytes_writer.buffer)
        # print(dir(bytes_writer.buffer))
        # assert(bytes_writer.getvalue() != raw_bytes), (bytes_writer.getvalue(), raw_bytes)
