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

from confluent_kafka import Producer, KafkaException
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

from producer import KafkaStatus

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


class AvroHandler(object):

    # Resetable interface for serializing messages with an avro schema.

    stream: io.BytesIO
    writer: DataFileWriter
    schema: spavro.schema

    def __init__(
        self,
        schema: spavro.schema
    ):
        self.schema = schema
        self.open()  # ready to serialize

    def close(self) -> None:
        self.writer.close()

    def open(self) -> None:
        try:
            self.writer.close()
        except AttributeError:
            pass
        self.stream = io.BytesIO()
        self.writer = DataFileWriter(
            self.stream,
            DatumWriter(),
            self.schema,
            codec='deflate'
        )

    def reset(self) -> None:
        self.open()

    def append(self, msg) -> None:
        self.writer.append(msg)

    def getvalue(self) -> bytes:
        self.writer.flush()
        return self.stream.getvalue()

    def validate(self, msg) -> bool:
        return validate(self.schema, msg)


class RedisProducer(object):

    # muted resource_ids
    ignored_decorator_ids: Dict[str, str]
    # packages sent to kafka but not acknowledged
    inflight: Set[str]
    # KafkaProducer
    producer: Producer
    # Redis Handler
    resoure_helper: ResourceHelper
    kafka_status: KafkaStatus = KafkaStatus.SUBMISSION_PENDING
    # SUBMISSION_PENDING = 1
    # SUBMISSION_FAILURE = 2
    # SUBMISSION_SUCCESS = 3

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
                    LOG.info(
                        f'NO-SAVE: {_id}'
                        f' | err {err.name()}'
                    )
                    self.kafka_status = KafkaStatus.SUBMISSION_FAILURE
                    try:
                        self.acknowledge_failure(_id)
                    except KeyError:
                        pass
                else:
                    if self.kafka_status is KafkaStatus.SUBMISSION_FAILURE:
                        LOG.critical(f'save after failure! -> {_id}')
                        raise KafkaException('Stopping Submissions!')
                    LOG.debug(f'SAVE: {_id}')
                    self.kafka_status = KafkaStatus.SUBMISSION_SUCCESS
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
    def wait_for_kafka(self, timeout=10):
        LOG.debug('Waiting for kafka acknowledgement.')
        with Timeout(timeout):
            try:
                while len(self.inflight) > 0:
                    LOG.debug(f'waiting for confirmation of '
                              f'{len(self.inflight)} messages')
                    sleep(.1)
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
        # keep this reasonably high since we need to flush between
        max_bundle_size: int = 250,
        # single produce topics can get ahead of themselves if not checked
        max_flush_interval: int = 1000,
        max_bundle_kbs: int = 50000
    ):
        topic: str
        serialize_mode: str  # single / multi
        schema: Schema
        try:
            topic, serialize_mode, schema = \
                self.get_production_options(decorator_id)
        except ValueError as ver:
            raise ver
        avro_schema = spavro.schema.parse(json.dumps(schema.schema))
        # we want to fail quickly if the broker isn't ready.
        # this value ramps up as we successfully send data to kafka
        # quickly reaching the maximum value `max_flush_interval`
        # to prioritize throughput while maintaining ordering guarantees
        flush_interval = 1
        try:
            avro_handler = AvroHandler(avro_schema)
            bundle: List[str] = []  # list of packaged but not sent _ids
            flush_count: int = 0
            bundle_kbs: int = 0
            for entity in entity_iterator:
                flush_count += 1
                if self.kafka_status == KafkaStatus.SUBMISSION_FAILURE:
                    LOG.info('Entities -> Kafka timed out. Stopping submission.')
                    # empty bundled but unsent items:
                    for _id in bundle:
                        self.inflight.remove(_id)
                    bundle = []
                    raise KafkaException('Broked did not accept submissions.')
                _id = entity.id
                msg = entity.payload
                offset = entity.offset
                if avro_handler.validate(msg):
                    # Message validates against current schema
                    LOG.debug(
                        "ENQUEUE MSG TOPIC: %s, ID: %s, MOD: %s" % (
                            topic,
                            _id,
                            offset
                        ))
                    if serialize_mode != 'single':
                        bundle_kbs += sys.getsizeof(str(msg))
                    bundle.append(_id)
                    # register as in flight
                    self.inflight.add(_id)
                    # add to bundle
                    avro_handler.append(msg)
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
                        avro_handler,
                        # only single mode messages can be keyed!
                        key=_id
                    )
                    bundle = []
                    if flush_count >= flush_interval:
                        self.producer.flush()
                        # increase this if we succeed
                        flush_interval = max(
                            [flush_interval * 2, max_flush_interval]
                        )
                        flush_count = 0
                elif len(bundle) == max_bundle_size  \
                        or bundle_kbs >= max_bundle_kbs:
                    # or when bundle is big enough
                    self.produce_bundle(
                        topic,
                        avro_handler
                    )
                    bundle_kbs = 0
                    previous_bundle = len(bundle)
                    bundle = []  # reset counter
                    # we need to flush with bundled assets to keep a strong
                    # guarentee of ordering
                    if flush_count >= flush_interval:
                        self.producer.flush()
                        # increase this if we succeed
                        flush_interval = max(
                            [flush_interval * 2, max_flush_interval/previous_bundle]
                        )
                        flush_count = 0
                    # self.producer.flush()

            if serialize_mode != 'single' \
                    and len(bundle) > 0:  # there's something to commit
                self.produce_bundle(topic, avro_handler)
                # we need to flush with bundled assets
                self.producer.flush()
        except Exception as err:
            LOG.error(err)
            raise err
        finally:
            avro_handler.close()

    # enqueue a single bundle for production, but do not wait (flush).
    def produce_bundle(
        self,
        topic: str,
        avro_handler: AvroHandler,
        key: str = None
    ):
        raw_bytes = avro_handler.getvalue()
        self.producer.produce(
            topic,
            raw_bytes,
            key=key,
            callback=self.kafka_callback
        )
        self.producer.poll(0)  # trigger delivery reports
        # clear old messages and reset the file handlers for the next round
        avro_handler.reset()
