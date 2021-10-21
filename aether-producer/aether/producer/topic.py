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

import ast
import enum
import gevent
import io
import json
import traceback
from typing import (Any, Dict, TYPE_CHECKING)

from datetime import datetime

from confluent_kafka import Producer
from confluent_kafka.admin import NewTopic

import spavro.schema
from spavro.datafile import DataFileWriter, DataFileReader
from spavro.io import DatumWriter, DatumReader
from spavro.io import validate

from aether.producer.db import Offset
from aether.producer.settings import SETTINGS, KAFKA_SETTINGS, get_logger

if TYPE_CHECKING:
    from aether.producer import ProducerManager

logger = get_logger('topic')


class SchemaWrapper(object):
    definition: Dict[str, Any]
    name: str
    offset: str  # current offset
    schema: spavro.schema.Schema
    schema_id: str
    realm: str
    topic: str
    operating_status: 'TopicStatus'

    def __init__(self, realm, name=None, schema_id=None, definition=None, aether_definition=None):
        self.realm = realm
        if aether_definition:
            self.name = aether_definition['schema_name']
            self.schema_id = aether_definition['schema_id']
        elif all([name, schema_id]):
            self.name = name
            self.schema_id = schema_id
        else:
            raise RuntimeError('Requires either name and id, or aether_definition')
        if any([definition, aether_definition]):
            self.update(aether_definition, definition)
        self.get_topic_name()
        self.operating_status = TopicStatus.NORMAL

    def definition_from_aether(self, aether_definition: Dict[str, Any]):
        return ast.literal_eval(json.dumps(aether_definition['schema_definition']))

    def is_equal(self, new_aether_definition) -> bool:
        return (
            json.dumps(self.definition_from_aether(new_aether_definition))
            == json.dumps(self.definition))

    def update(self, aether_definition: Dict[str, Any] = None, definition: Dict[str, Any] = None):
        if not any([aether_definition, definition]):
            raise RuntimeError('Expected one of [definition, aether_definition]')
        if aether_definition:
            self.definition = self.definition_from_aether(aether_definition)
        elif definition:
            self.definition = definition
        self.schema = spavro.schema.parse(json.dumps(self.definition))

    def get_topic_name(self):
        topic_base = SETTINGS.get('topic_settings', {}).get('name_modifier', '%s') % self.name
        self.topic = f'{self.realm}.{topic_base}'


class TopicStatus(enum.Enum):
    INITIALIZING = 0  # Started by not yet operational
    PAUSED = 1        # Paused
    LOCKED = 2        # Paused by system and non-resumable via API until sys unlock
    REBUILDING = 3    # Topic is being rebuilt
    NORMAL = 4        # Topic is operating normally
    ERROR = 5


class RealmManager(object):

    # Creates a long running job on RealmManager.update_kafka

    def __init__(self, context: 'ProducerManager', realm: str):
        self.context = context
        self.realm = realm
        self.sleep_time = int(SETTINGS.get('sleep_time', 10))
        self.window_size_sec = int(SETTINGS.get('window_size_sec', 3))
        self.kafka_failure_wait_time = float(SETTINGS.get('kafka_failure_wait_time', 10))
        self.status = {}
        self.schemas = {}
        self.known_topics = []
        self.get_producer()
        # Spawn worker and give to pool.
        self.context.threads.append(gevent.spawn(self.update_loop))

    def update_topics(self):
        self.known_topics = [t for t in self.producer.list_topics().topics.keys()]

    def create_topic(self, topic=None, topics=None):
        topic_objects = []
        if not topics:
            topics = [topic]

        topic_config = SETTINGS.get('kafka_settings', {}).get('default.topic.config')
        partitions = int(SETTINGS.get('kafka_default_topic_partitions', 1))
        replicas = int(SETTINGS.get('kafka_default_topic_replicas', 1))

        for t in topics:
            logger.debug(f'Trying to create topic {t}')
            topic_objects.append(
                NewTopic(
                    t,
                    num_partitions=partitions,
                    replication_factor=replicas,
                    config=topic_config,
                )
            )

        kadmin = self.context.kafka_admin_client
        kadmin.create_topics(topic_objects)

    def get_producer(self):
        self.producer = Producer(**KAFKA_SETTINGS)
        logger.debug(f'Producer for {self.realm} started...')

    # API for realm status

    def get_status(self):
        # Updates inflight status and returns to Flask called
        for sw in self.schemas.values():
            self.status[sw.name]['operating_status'] = str(sw.operating_status)
        return self.status

    # API Calls to Control Topic

    def pause(self, sw: SchemaWrapper):
        # Stops sending of data on this topic until resume is called or Producer restarts.
        if sw.operating_status is not TopicStatus.NORMAL:
            logger.info(f'Topic {sw.name} could not pause, status: {sw.operating_status}.')
            return False

        logger.info(f'Topic {sw.name} is pausing.')
        sw.operating_status = TopicStatus.PAUSED
        return True

    def resume(self, sw: SchemaWrapper):
        # Resume sending data after pausing.
        if sw.operating_status is not TopicStatus.PAUSED:
            logger.info(f'Topic {sw.name} could not resume, status: {sw.operating_status}.')
            return False

        logger.info(f'Topic {sw.name} is resuming.')
        sw.operating_status = TopicStatus.NORMAL
        return True

    # Functions to rebuild this topic

    def rebuild(self, sw: SchemaWrapper):
        # API Call
        logger.warn(f'Topic {sw.name} is being REBUILT!')
        # kick off rebuild process
        _fn = self._make_rebuild_process(sw)
        self.context.threads.append(gevent.spawn(_fn))
        return True

    def _make_rebuild_process(self, sw: SchemaWrapper):

        def fn():
            # greened background task to handle rebuilding of topic
            sw.operating_status = TopicStatus.REBUILDING
            tag = f'REBUILDING {sw.topic}:'
            sleep_time = self.sleep_time * 1.5
            logger.info(f'{tag} waiting {sleep_time}(sec) for inflight ops to resolve')
            self.context.safe_sleep(sleep_time)
            logger.info(f'{tag} Deleting Topic')

            if not self.delete_this_topic(sw):
                logger.warning(f'{tag} FAILED. Topic will not resume.')
                sw.operating_status = TopicStatus.LOCKED
                return

            logger.warn(f'{tag} Resetting Offset.')
            self.set_offset('', sw)
            logger.info(f'{tag} Rebuilding Topic Producer')
            logger.warn(f'{tag} Wipe Complete. /resume to complete operation.')
            sw.operating_status = TopicStatus.PAUSED
        return fn

    def delete_this_topic(self, sw: SchemaWrapper):
        kadmin = self.context.kafka_admin_client
        fs = kadmin.delete_topics([sw.topic], operation_timeout=60)
        future = fs.get(sw.topic)
        for x in range(60):
            if not future.done():
                if (x % 5 == 0):
                    logger.debug(f'REBUILDING {sw.topic}: Waiting for future to complete')
                self.context.safe_sleep(1)
            else:
                return True
        return False

    # Get Data for a Topic from Kernel

    def updates_available(self, sw: SchemaWrapper):
        return self.context.kernel_client.check_updates(sw.realm, sw.schema_id, sw.name, sw.offset)

    def get_db_updates(self, sw: SchemaWrapper):
        return self.context.kernel_client.get_updates(sw.realm, sw.schema_id, sw.name, sw.offset)

    def get_topic_size(self, sw: SchemaWrapper):
        return self.context.kernel_client.count_updates(sw.realm, sw.schema_id, sw.name)

    # Updates

    # # Main Loop

    def update_loop(self):
        while not self.context.killed:
            self.context.thread_checkin(self.realm)
            logger.info(f'Looking for updates on: {self.realm}')
            self.producer.poll(0)
            self.update_schemas()
            res = 0
            for sw in self.schemas.values():
                res += self.update_kafka(sw) or 0
            if res:
                self.context.safe_sleep(1)  # yield instead of waiting for flush
                self.producer.flush(timeout=20)
            else:
                logger.info(f'No updates on: {self.realm}')
            self.context.safe_sleep(self.sleep_time)  # wait for next batch

    # # Schema Update

    def update_schemas(self):
        schemas = self.context.kernel_client.get_schemas(realm=self.realm)
        self.update_topics()
        new_topics = []
        for aether_definition in schemas:
            schema_name = aether_definition['schema_name']
            if schema_name not in self.schemas:
                self.schemas[schema_name] = SchemaWrapper(
                    self.realm, aether_definition=aether_definition
                )
                self.status[schema_name] = {}
                topic = self.schemas[schema_name].topic
                if topic not in self.known_topics:
                    new_topics.append(topic)

            else:
                if not self.schemas[schema_name].is_equal(aether_definition):
                    self.schemas[schema_name].update(aether_definition=aether_definition)
        if new_topics:
            self.create_topic(topics=new_topics)

    # # Kafka Publish

    def update_kafka(self, sw: SchemaWrapper):
        # Main update loop
        # Monitors postgres for changes via RealmManager.updates_available
        # Consumes updates to the Postgres DB via RealmManager.get_db_updates
        # Sends new messages to Kafka
        # Registers message callback (ok or fail) to RealmManager.kafka_callback
        logger.debug(f'Checking {sw.topic}')

        if sw.operating_status is TopicStatus.INITIALIZING:
            logger.debug(f'Waiting for topic {sw.topic} to initialize...')
            return

        if sw.operating_status is not TopicStatus.NORMAL:
            logger.debug(
                f'Topic {sw.topic} not updating, status: {sw.operating_status}'
                f', waiting {self.sleep_time}(sec)')
            return

        if not self.context.kafka_available():
            logger.debug('Kafka Container not accessible, waiting.')
            return

        sw.offset = self.get_offset(sw) or ''

        if not self.updates_available(sw):
            logger.debug(f'No updates on {sw.topic}')
            return

        try:
            logger.debug(f'Getting Changeset for {sw.topic}')
            new_rows = self.get_db_updates(sw)
            if not new_rows:
                logger.debug(f'No changes on {sw.topic}')
                return
            end_offset = new_rows[-1].get('modified')
        except Exception as pge:
            logger.warning(f'Could not get new records from kernel: {pge}')
            return

        try:
            with io.BytesIO() as bytes_writer:
                writer = DataFileWriter(
                    bytes_writer, DatumWriter(), sw.schema, codec='deflate')

                for row in new_rows:
                    _id = row['id']
                    msg = row.get('payload')
                    modified = row.get('modified')
                    if validate(sw.schema, msg):
                        # Message validates against current schema
                        logger.debug(
                            f'ENQUEUE MSG TOPIC: {sw.topic}, ID: {_id}, MOD: {modified}')
                        writer.append(msg)
                    else:
                        # Message doesn't have the proper format for the current schema.
                        logger.warning(
                            f'SCHEMA_MISMATCH: NOT SAVED! TOPIC: {sw.topic}, ID: {_id}')

                writer.flush()
                raw_bytes = bytes_writer.getvalue()

            self.producer.produce(
                sw.topic,
                raw_bytes,
                callback=self._make_kafka_callback(sw, end_offset)
            )
            return len(new_rows)

        except Exception as ke:
            logger.warning(f'error in Kafka save: {ke}')
            logger.warning(traceback.format_exc())

    # Callbacks

    def _make_kafka_callback(self, sw: SchemaWrapper, end_offset):

        def _callback(err=None, msg=None, _=None, **kwargs):
            if err:
                logger.warning(f'ERROR [{err}, {msg}, {kwargs}]')
                return self._kafka_failed(sw, err, msg)
            return self._kafka_ok(sw, end_offset, msg)

        return _callback

    def _kafka_ok(self, sw: SchemaWrapper, end_offset, msg):
        _change_size = 0
        with io.BytesIO() as obj:
            obj.write(msg.value())
            reader = DataFileReader(obj, DatumReader())
            _change_size = sum([1 for i in reader])
            logger.info(f'saved {_change_size} messages in topic {sw.topic}. Offset: {end_offset}')
        self.set_offset(end_offset, sw)
        self.status[sw.name]['last_changeset_status'] = {
            'changes': _change_size,
            'failed': 0,
            'succeeded': _change_size,
            'timestamp': datetime.now().isoformat(),
        }

    def _kafka_failed(self, sw: SchemaWrapper, err, msg):
        _change_size = 0
        with io.BytesIO() as obj:
            obj.write(msg.value())
            reader = DataFileReader(obj, DatumReader())
            for message in reader:
                _change_size += 1
                _id = message.get('id')
                logger.debug(f'NO-SAVE: {_id} in topic {sw.topic} | err {err.name()}')
        last_error_set = {
            'changes': _change_size,
            'failed': _change_size,
            'succeeded': 0,
            'errors': str(err),
            'outcome': 'RETRY',
            'timestamp': datetime.now().isoformat(),
        }
        self.status[sw.name]['last_errors_set'] = last_error_set
        self.context.kafka_last_submission_error = last_error_set['timestamp']

    def get_offset(self, sw: SchemaWrapper):
        # Get current offset from Database
        offset = Offset.get_offset(sw.schema_id)
        if offset:
            logger.debug(f'Got offset for {sw.topic} | {offset}')
            return offset
        else:
            logger.debug(f'Could not get offset for {sw.topic}, checking legacy names')
            return self._migrate_legacy_offset(sw) or None

    def set_offset(self, offset, sw: SchemaWrapper):
        # Set a new offset in the database
        new_offset = Offset.update(sw.schema_id, offset)
        logger.debug(f'Set new offset for {sw.topic} | {new_offset}')
        self.status['offset'] = new_offset

    # handles move from {AetherName} which can collide over realms -> schema_id which should not
    # and is what we use to query the entities anyway
    def _migrate_legacy_offset(self, sw: SchemaWrapper):
        old_offset = Offset.get_offset(sw.name)
        if old_offset:
            logger.warn(f'Found legacy offset for id: {sw.schema_id} at {sw.name}: {old_offset}')
            self.set_offset(old_offset, sw)
            logger.warn(f'Migrated offset {sw.name} -> {sw.schema_id}')
            return old_offset
        return None
