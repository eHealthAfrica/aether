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
import concurrent
import enum
import gevent
import io
import json
import sys
import traceback
from datetime import datetime

from confluent_kafka import Producer
from confluent_kafka.admin import NewTopic

import spavro.schema
from spavro.datafile import DataFileWriter, DataFileReader
from spavro.io import DatumWriter, DatumReader
from spavro.io import validate

from producer.db import Offset
from producer.settings import SETTINGS, KAFKA_SETTINGS, get_logger

logger = get_logger('producer-topic')


class KafkaStatus(enum.Enum):
    SUBMISSION_PENDING = 1
    SUBMISSION_FAILURE = 2
    SUBMISSION_SUCCESS = 3


class TopicStatus(enum.Enum):
    INITIALIZING = 0  # Started by not yet operational
    PAUSED = 1        # Paused
    LOCKED = 2        # Paused by system and non-resumable via API until sys unlock
    REBUILDING = 3    # Topic is being rebuilt
    NORMAL = 4        # Topic is operating normally
    ERROR = 5


class TopicManager(object):

    # Creates a long running job on TopicManager.update_kafka

    def __init__(self, context, schema, realm):
        self.context = context
        self.name = schema['schema_name']
        self.realm = realm
        self.offset = ''
        self.operating_status = TopicStatus.INITIALIZING
        self.status = {
            'last_errors_set': {},
            'last_changeset_status': {}
        }
        self.change_set = {}
        self.successful_changes = []
        self.failed_changes = {}
        self.wait_time = SETTINGS.get('sleep_time', 2)
        self.window_size_sec = SETTINGS.get('window_size_sec', 3)

        self.kafka_failure_wait_time = SETTINGS.get('kafka_failure_wait_time', 10)

        try:
            topic_base = SETTINGS.get('topic_settings', {}).get('name_modifier', '%s') % self.name
            self.topic_name = f'{self.realm}.{topic_base}'
        except Exception:  # Bad Name
            logger.critical((f'invalid name_modifier using topic name for topic: {self.name}.'
                             ' Update configuration for topic_settings.name_modifier'))
            # This is a failure which could cause topics to collide. We'll kill the producer
            # so the configuration can be updated.
            sys.exit(1)

        self.update_schema(schema)
        self.get_producer()
        # Spawn worker and give to pool.
        logger.debug(f'Spawning kafka update thread: {self.topic_name}')
        self.context.threads.append(gevent.spawn(self.update_kafka))
        logger.debug(f'Checking for existence of topic {self.topic_name}')
        while not self.check_topic():
            if self.create_topic():
                break
            logger.debug(f'Waiting 30 seconds to retry creation of topic {self.topic_name}')
            self.context.safe_sleep(30)
        self.operating_status = TopicStatus.NORMAL

    def check_topic(self):
        topics = [t for t in self.producer.list_topics().topics.keys()]
        if self.topic_name in topics:
            logger.debug(f'Topic {self.topic_name} already exists.')
            return True

        logger.debug(f'Topic {self.name} does not exist. current topics: {topics}')
        return False

    def create_topic(self):
        logger.debug(f'Trying to create topic {self.topic_name}')

        kadmin = self.context.kafka_admin_client
        topic_config = SETTINGS.get('kafka_settings', {}).get('default.topic.config')
        partitions = int(SETTINGS.get('kafka_default_topic_partitions', 1))
        replicas = int(SETTINGS.get('kafka_default_topic_replicas', 1))
        topic = NewTopic(
            self.topic_name,
            num_partitions=partitions,
            replication_factor=replicas,
            config=topic_config,
        )
        fs = kadmin.create_topics([topic])
        # future must return before timeout
        for f in concurrent.futures.as_completed(iter(fs.values()), timeout=60):
            e = f.exception()
            if not e:
                logger.info(f'Created topic {self.name}')
                return True
            else:
                logger.critical(f'Topic {self.name} could not be created: {e}')
                return False

    def get_producer(self):
        self.producer = Producer(**KAFKA_SETTINGS)
        logger.debug(f'Producer for {self.name} started...')

    # API Calls to Control Topic

    def pause(self):
        # Stops sending of data on this topic until resume is called or Producer restarts.
        if self.operating_status is not TopicStatus.NORMAL:
            logger.info(f'Topic {self.name} could not pause, status: {self.operating_status}.')
            return False

        logger.info(f'Topic {self.name} is pausing.')
        self.operating_status = TopicStatus.PAUSED
        return True

    def resume(self):
        # Resume sending data after pausing.
        if self.operating_status is not TopicStatus.PAUSED:
            logger.info(f'Topic {self.name} could not resume, status: {self.operating_status}.')
            return False

        logger.info(f'Topic {self.name} is resuming.')
        self.operating_status = TopicStatus.NORMAL
        return True

    # Functions to rebuilt this topic

    def rebuild(self):
        # API Call
        logger.warn(f'Topic {self.name} is being REBUIT!')
        # kick off rebuild process
        self.context.threads.append(gevent.spawn(self.handle_rebuild))
        return True

    def handle_rebuild(self):
        # greened background task to handle rebuilding of topic
        self.operating_status = TopicStatus.REBUILDING
        tag = f'REBUILDING {self.name}:'
        logger.info(f'{tag} waiting {self.wait_time *1.5}(sec) for inflight ops to resolve')
        self.context.safe_sleep(int(self.wait_time * 1.5))
        logger.info(f'{tag} Deleting Topic')
        self.producer = None

        if not self.delete_this_topic():
            logger.critical(f'{tag} FAILED. Topic will not resume.')
            self.operating_status = TopicStatus.LOCKED
            return

        logger.warn(f'{tag} Resetting Offset.')
        self.set_offset('')
        logger.info(f'{tag} Rebuilding Topic Producer')
        self.producer = Producer(**KAFKA_SETTINGS)
        logger.warn(f'{tag} Wipe Complete. /resume to complete operation.')
        self.operating_status = TopicStatus.PAUSED

    def delete_this_topic(self):
        kadmin = self.context.kafka_admin_client
        fs = kadmin.delete_topics([self.name], operation_timeout=60)
        future = fs.get(self.name)
        for x in range(60):
            if not future.done():
                if (x % 5 == 0):
                    logger.debug(f'REBUILDING {self.name}: Waiting for future to complete')
                gevent.sleep(1)
            else:
                return True
        return False

    def updates_available(self):
        return self.context.kernel_client.check_updates(self.offset, self.name, self.realm)

    def get_db_updates(self):
        return self.context.kernel_client.get_updates(self.offset, self.name, self.realm)

    def get_topic_size(self):
        return self.context.kernel_client.count_updates(self.name, self.realm)

    def update_schema(self, schema_obj):
        self.schema_obj = self.parse_schema(schema_obj)
        self.schema = spavro.schema.parse(json.dumps(self.schema_obj))

    def parse_schema(self, schema_obj):
        # We split this method from update_schema because schema_obj as it is can not
        # be compared for differences. literal_eval fixes this. As such, this is used
        # by the schema_changed() method.
        # schema_obj is a nested OrderedDict, which needs to be stringified
        return ast.literal_eval(json.dumps(schema_obj['schema_definition']))

    def schema_changed(self, schema_candidate):
        # for use by ProducerManager.check_schemas()
        return self.parse_schema(schema_candidate) != self.schema_obj

    def get_status(self):
        # Updates inflight status and returns to Flask called
        self.status['operating_status'] = str(self.operating_status)
        self.status['inflight'] = [i for i in self.change_set.keys()]
        return self.status

    # Callback function registered with Kafka Producer to acknowledge receipt
    def kafka_callback(self, err=None, msg=None, _=None, **kwargs):
        if err:
            logger.error(f'ERROR [{err}, {msg}, {kwargs}]')

        with io.BytesIO() as obj:
            obj.write(msg.value())
            reader = DataFileReader(obj, DatumReader())
            for message in reader:
                _id = message.get('id')
                if err:
                    logger.debug(f'NO-SAVE: {_id} in topic {self.topic_name} | err {err.name()}')
                    self.failed_changes[_id] = err
                else:
                    logger.debug(f'SAVE: {_id} in topic {self.topic_name}')
                    self.successful_changes.append(_id)

    def update_kafka(self):
        # Main update loop
        # Monitors postgres for changes via TopicManager.updates_available
        # Consumes updates to the Posgres DB via TopicManager.get_db_updates
        # Sends new messages to Kafka
        # Registers message callback (ok or fail) to TopicManager.kafka_callback
        # Waits for all messages to be accepted or timeout in TopicManager.wait_for_kafka
        logger.debug(f'Topic {self.name}: Initializing')

        while self.operating_status is TopicStatus.INITIALIZING:
            if self.context.killed:
                return
            logger.debug(f'Waiting for topic {self.name} to initialize...')
            self.context.safe_sleep(self.wait_time)
            pass

        while not self.context.killed:
            if self.operating_status is not TopicStatus.NORMAL:
                logger.debug(
                    f'Topic {self.name} not updating, status: {self.operating_status}'
                    + f', waiting {self.wait_time}(sec)')
                self.context.safe_sleep(self.wait_time)
                continue

            if not self.context.kafka_available():
                logger.debug('Kafka Container not accessible, waiting.')
                self.context.safe_sleep(self.wait_time)
                continue

            self.offset = self.get_offset() or ''
            if not self.updates_available():
                logger.debug('No updates')
                self.context.safe_sleep(self.wait_time)
                continue

            try:
                logger.debug(f'Getting Changeset for {self.name}')
                self.change_set = {}
                new_rows = self.get_db_updates()
                if not new_rows:
                    self.context.safe_sleep(self.wait_time)
                    continue

                end_offset = new_rows[-1].get('modified')
            except Exception as pge:
                logger.error(f'Could not get new records from kernel: {pge}')
                self.context.safe_sleep(self.wait_time)
                continue

            try:
                with io.BytesIO() as bytes_writer:
                    writer = DataFileWriter(
                        bytes_writer, DatumWriter(), self.schema, codec='deflate')

                    for row in new_rows:
                        _id = row['id']
                        msg = row.get('payload')
                        modified = row.get('modified')
                        if validate(self.schema, msg):
                            # Message validates against current schema
                            logger.debug(
                                f'ENQUEUE MSG TOPIC: {self.name}, ID: {_id}, MOD: {modified}')
                            self.change_set[_id] = row
                            writer.append(msg)
                        else:
                            # Message doesn't have the proper format for the current schema.
                            logger.critical(
                                f'SCHEMA_MISMATCH: NOT SAVED! TOPIC: {self.name}, ID: {_id}')

                    writer.flush()
                    raw_bytes = bytes_writer.getvalue()

                self.producer.poll(0)
                self.producer.produce(
                    self.topic_name,
                    raw_bytes,
                    callback=self.kafka_callback
                )
                self.producer.flush()
                self.wait_for_kafka(end_offset, failure_wait_time=self.kafka_failure_wait_time)

            except Exception as ke:
                logger.error(f'error in Kafka save: {ke}')
                logger.error(traceback.format_exc())
                self.context.safe_sleep(self.wait_time)

    def wait_for_kafka(self, end_offset, timeout=10, iters_per_sec=10, failure_wait_time=10):
        # Waits for confirmation of message receipt from Kafka before moving to next changeset
        # Logs errors and status to log and to web interface

        sleep_time = timeout / (timeout * iters_per_sec)
        change_set_size = len(self.change_set)
        errors = {}
        for i in range(timeout * iters_per_sec):
            # whole changeset failed; systemic failure likely; sleep it off and try again
            if len(self.failed_changes) >= change_set_size:
                self.handle_kafka_errors(change_set_size, True, failure_wait_time)
                self.clear_changeset()
                logger.info(
                    f'Changeset not saved; likely broker outage, sleeping worker for {self.name}')
                self.context.safe_sleep(failure_wait_time)
                return  # all failed; ignore changeset

            # All changes were saved
            elif len(self.successful_changes) == change_set_size:
                logger.debug(f'All changes saved ok in topic {self.name}.')
                break

            # Remove successful and errored changes
            for k in self.failed_changes:
                try:
                    del self.change_set[k]
                except KeyError:
                    pass  # could have been removed on previous iter

            for k in self.successful_changes:
                try:
                    del self.change_set[k]
                except KeyError:
                    pass  # could have been removed on previous iter

            # All changes registered
            if len(self.change_set) == 0:
                break

            gevent.sleep(sleep_time)

        # Timeout reached or all messages returned ( and not all failed )

        self.status['last_changeset_status'] = {
            'changes': change_set_size,
            'failed': len(self.failed_changes),
            'succeeded': len(self.successful_changes),
            'timestamp': datetime.now().isoformat(),
        }
        if errors:
            self.handle_kafka_errors(change_set_size, all_failed=False)
        self.clear_changeset()
        # Once we're satisfied, we set the new offset past the processed messages
        self.context.kafka = KafkaStatus.SUBMISSION_SUCCESS
        self.set_offset(end_offset)
        # Sleep so that elements passed in the current window become eligible
        self.context.safe_sleep(self.window_size_sec)

    def handle_kafka_errors(self, change_set_size, all_failed=False, failure_wait_time=10):
        # Errors in saving data to Kafka are handled and logged here
        errors = {}
        for _id, err in self.failed_changes.items():
            # accumulate error types
            error_type = str(err.name())
            errors[error_type] = errors.get(error_type, 0) + 1

        last_error_set = {
            'changes': change_set_size,
            'errors': errors,
            'outcome': 'RETRY',
            'timestamp': datetime.now().isoformat(),
        }

        if not all_failed:
            # Collect Error types for reporting
            for _id, err in self.failed_changes.items():
                logger.critical(f'PRODUCER_FAILURE: T: {self.name} ID {_id}, ERR_MSG {err.name()}')

            dropped_messages = change_set_size - len(self.successful_changes)
            errors['NO_REPLY'] = dropped_messages - len(self.failed_changes)

            last_error_set['failed'] = len(self.failed_changes)
            last_error_set['succeeded'] = len(self.successful_changes)
            last_error_set['outcome'] = f'MSGS_DROPPED : {dropped_messages}'

        self.status['last_errors_set'] = last_error_set
        if all_failed:
            self.context.kafka = KafkaStatus.SUBMISSION_FAILURE
        return

    def clear_changeset(self):
        self.failed_changes = {}
        self.successful_changes = []
        self.change_set = {}

    def get_offset(self):
        # Get current offset from Database
        offset = Offset.get_offset(self.name)
        if offset:
            logger.debug(f'Got offset for {self.name} | {offset}')
            return offset
        else:
            logger.debug(f'Could not get offset for {self.name}, it is a new type')
            # No valid offset so return None; query will use empty string which is < any value
            return None

    def set_offset(self, offset):
        # Set a new offset in the database
        new_offset = Offset.update(self.name, offset)
        logger.debug(f'Set new offset for {self.name} | {new_offset}')
        self.status['offset'] = new_offset
