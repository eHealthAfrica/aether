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

from datetime import datetime
import io
import json
import spavro
from spavro.datafile import DataFileWriter
from spavro.io import DatumWriter, validate
from typing import (
    Dict,
    Iterator,
    List,
    Tuple,
    Union
)

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


class RedisProducer(object):

    resoure_helper: ResourceHelper
    ignored_decorator_ids: Dict[str, str]
    inflight_operations: List[str]

    @classmethod
    def get_entity_key(cls, e: Entity) -> str:
        return f'{e.offset}/{e.decorator_id}/{e.id}'

    @classmethod
    def get_entity_key_parts(cls, key: str) -> List[str]:
        return key.split('/')  # offset, decorator_id, entity_id

    def __init__(self, resoure_helper: ResourceHelper):
        self.resoure_helper = resoure_helper
        self.ignored_decorator_ids = {}

    def ignore_entity_type(self, decorator_id: str) -> None:
        self.ignored_decorator_ids[decorator_id] = datetime.now().isoformat()

    def unignore_entity_type(self, decorator_id: str) -> None:
        del self.ignored_decorator_ids[decorator_id]

    def get_entity_keys(
        self,
        ignored_decorators: Union[List[str], None] = None
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
        return valid_keys

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
        topic = f'{d.tenant}:{d.topic_name}'
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
            offset, decorator_id, entity_id = RedisProducer.get_entity_key_parts(key)
            try:
                decorator_info[decorator_id].append(offset)
                entities[decorator_id].append(entity_id)
            except KeyError:
                decorator_info[decorator_id] = [offset]
                entities[decorator_id] = [entity_id]
        for _id, offsets in decorator_info.items():
            start = min(offsets)
            end = max(offsets)
            LOG.debug(
                f'Preparing produce of {_id}'
                f'for offsets: {start} -> {end}'
            )
            entity_iterator = self.get_entity_generator(entities[_id])
            self.produce_topic(_id, entity_iterator)
        # self.producer.flush()
        # self.wait_for_kafka(
        #     end_offset, failure_wait_time=self.kafka_failure_wait_time)

    def produce_topic(
        self,
        decorator_id: str,
        entity_iterator: Iterator[Entity]
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

                for entity in entity_iterator:
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
                        self.produce_bundle(topic, writer, bytes_writer)
                if serialize_mode != 'single':
                    # TODO handle callback for bundled assets
                    self.produce_bundle(topic, writer, bytes_writer)
        except Exception as err:
            LOG.critical(err)

    def produce_bundle(
        self,
        topic: str,
        writer: DataFileWriter,
        bytes_writer: io.BytesIO
    ):
        writer.flush()
        # raw_bytes = bytes_writer.getvalue()
        # self.producer.produce(
        #     topic,
        #     raw_bytes,
        #     callback=self.kafka_callback
        # )
        bytes_writer.flush()
        assert(bytes_writer.getvalue() is None)
