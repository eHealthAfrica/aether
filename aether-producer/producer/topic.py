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

from gevent import monkey, sleep

# need to patch sockets to make requests async
monkey.patch_all()  # noqa
import psycogreen.gevent
psycogreen.gevent.patch_psycopg()  # noqa

import ast
import concurrent
import enum
import io
import json
import sys
import traceback
from datetime import datetime

from confluent_kafka import Producer
from confluent_kafka.admin import NewTopic

import gevent

import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor

import spavro.schema
from spavro.datafile import DataFileWriter, DataFileReader
from spavro.io import DatumWriter, DatumReader
from spavro.io import validate

from producer.db import Offset
from producer.kernel import KERNEL_DB as POSTGRES
from producer.settings import SETTINGS, KAFKA_SETTINGS, KafkaStatus


class TopicStatus(enum.Enum):
    INITIALIZING = 0  # Started by not yet operational
    PAUSED = 1        # Paused
    LOCKED = 2        # Paused by system and non-resumable via API until sys unlock
    REBUILDING = 3    # Topic is being rebuilt
    NORMAL = 4        # Topic is operating normally
    ERROR = 5


class TopicManager(object):

    # Creates a long running job on TopicManager.update_kafka

    # Changes detection query
    NEW_STR = '''
        SELECT id, modified
        FROM kernel_entity_vw
        WHERE modified    > {modified}
          AND schema_name = {schema_name}
          AND realm       = {realm}
        LIMIT 1;
    '''

    # Count how many unique (controlled by kernel) messages should currently be in this topic
    COUNT_STR = '''
        SELECT COUNT(id)
        FROM kernel_entity_vw
        WHERE schema_name = {schema_name}
          AND realm       = {realm};
    '''

    # Changes pull query
    QUERY_STR = '''
        SELECT *
        FROM kernel_entity_vw
        WHERE modified    > {modified}
          AND schema_name = {schema_name}
          AND realm       = {realm}
        ORDER BY modified ASC
        LIMIT {limit};
    '''

    def __init__(self, context, schema, realm):
        self.context = context
        self.logger = self.context.logger
        self.name = schema['schema_name']
        self.realm = realm
        self.offset = ''
        self.operating_status = TopicStatus.INITIALIZING
        self.limit = SETTINGS.get('postgres_pull_limit', 100)
        self.status = {
            'last_errors_set': {},
            'last_changeset_status': {}
        }
        self.change_set = {}
        self.successful_changes = []
        self.failed_changes = {}
        self.wait_time = SETTINGS.get('sleep_time', 2)
        self.window_size_sec = SETTINGS.get('window_size_sec', 3)
        pg_requires = ['user', 'dbname', 'port', 'host', 'password']
        self.pg_creds = {key: SETTINGS.get(
            'postgres_%s' % key) for key in pg_requires}
        self.kafka_failure_wait_time = SETTINGS.get(
            'kafka_failure_wait_time', 10)
        try:
            topic_base = SETTINGS \
                .get('topic_settings', {}) \
                .get('name_modifier', '%s') \
                % self.name
            self.topic_name = f'{self.realm}.{topic_base}'
        except Exception:  # Bad Name
            self.logger.critical(('invalid name_modifier using topic name for topic: %s.'
                                  ' Update configuration for'
                                  ' topic_settings.name_modifier') % self.name)
            # This is a failure which could cause topics to collide. We'll kill the producer
            # so the configuration can be updated.
            sys.exit(1)
        self.update_schema(schema)
        self.get_producer()
        # Spawn worker and give to pool.
        self.logger.debug(f'Spawning kafka update thread: {self.topic_name}')
        self.context.threads.append(gevent.spawn(self.update_kafka))
        self.logger.debug(f'Checking for existence of topic {self.topic_name}')
        while not self.check_topic():
            if self.create_topic():
                break
            self.logger.debug(f'Waiting 30 seconds to retry creation of T:{self.topic_name}')
            self.context.safe_sleep(30)
        self.operating_status = TopicStatus.NORMAL

    def check_topic(self):
        metadata = self.producer.list_topics()
        topics = [t for t in metadata.topics.keys()]
        if self.topic_name in topics:
            self.logger.debug(f'Topic {self.topic_name} already exists.')
            return True
        self.logger.debug(f'Topic {self.name} does not exist. current topics: {topics}')
        return False

    def create_topic(self):
        self.logger.debug(f'Trying to create topic {self.topic_name}')
        kadmin = self.context.kafka_admin_client
        topic_config = SETTINGS.get('kafka_settings', {}).get('default.topic.config')
        partitions = int(SETTINGS.get('kafka_default_topic_partitions', 1))
        replicas = int(SETTINGS.get('kafka_default_topic_replicas', 1))
        topic = NewTopic(
            self.topic_name,
            num_partitions=partitions,
            replication_factor=replicas,
            config=topic_config
        )
        fs = kadmin.create_topics([topic])
        # future must return before timeout
        for f in concurrent.futures.as_completed(iter(fs.values()), timeout=60):
            e = f.exception()
            if not e:
                self.logger.info(f'Created topic {self.name}')
                return True
            else:
                self.logger.critical(f'Topic {self.name} could not be created: {e}')
                return False

    def get_producer(self):
        self.producer = Producer(**KAFKA_SETTINGS)
        self.logger.debug(f'Producer for {self.name} started...')

    # API Calls to Control Topic

    def pause(self):
        # Stops sending of data on this topic until resume is called or Producer restarts.
        if self.operating_status is not TopicStatus.NORMAL:
            self.logger.info(
                f'Topic {self.name} could not pause, status: {self.operating_status}.')
            return False
        self.logger.info(f'Topic {self.name} is pausing.')
        self.operating_status = TopicStatus.PAUSED
        return True

    def resume(self):
        # Resume sending data after pausing.
        if self.operating_status is not TopicStatus.PAUSED:
            self.logger.info(
                f'Topic {self.name} could not resume, status: {self.operating_status}.')
            return False
        self.logger.info(f'Topic {self.name} is resuming.')
        self.operating_status = TopicStatus.NORMAL
        return True

    # Functions to rebuilt this topic

    def rebuild(self):
        # API Call
        self.logger.warn(f'Topic {self.name} is being REBUIT!')
        # kick off rebuild process
        self.context.threads.append(gevent.spawn(self.handle_rebuild))
        return True

    def handle_rebuild(self):
        # greened background task to handle rebuilding of topic
        self.operating_status = TopicStatus.REBUILDING
        tag = f'REBUILDING {self.name}:'
        self.logger.info(f'{tag} waiting'
                         f' {self.wait_time *1.5}(sec) for inflight ops to resolve')
        self.context.safe_sleep(int(self.wait_time * 1.5))
        self.logger.info(f'{tag} Deleting Topic')
        self.producer = None

        if not self.delete_this_topic():
            self.logger.critical(f'{tag} FAILED. Topic will not resume.')
            self.operating_status = TopicStatus.LOCKED
            return

        self.logger.warn(f'{tag} Resetting Offset.')
        self.set_offset('')
        self.logger.info(f'{tag} Rebuilding Topic Producer')
        self.producer = Producer(**KAFKA_SETTINGS)
        self.logger.warn(f'{tag} Wipe Complete. /resume to complete operation.')
        self.operating_status = TopicStatus.PAUSED

    def delete_this_topic(self):
        kadmin = self.context.kafka_admin_client
        fs = kadmin.delete_topics([self.name], operation_timeout=60)
        future = fs.get(self.name)
        for x in range(60):
            if not future.done():
                if (x % 5 == 0):
                    self.logger.debug(f'REBUILDING {self.name}: Waiting for future to complete')
                sleep(1)
            else:
                return True
        return False

    # Postgres Facing Polls and handlers

    def updates_available(self):

        modified = '' if not self.offset else self.offset  # "" evals to < all strings
        query = sql.SQL(TopicManager.NEW_STR).format(
            modified=sql.Literal(modified),
            schema_name=sql.Literal(self.name),
            realm=sql.Literal(self.realm)
        )
        try:
            promise = POSTGRES.request_connection(1, self.name)  # Medium priority
            conn = promise.get()
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(query)
            return sum([1 for i in cursor]) > 0
        except psycopg2.OperationalError as pgerr:
            self.logger.critical(
                'Could not access Database to look for updates: %s' % pgerr)
            return False
        finally:
            try:
                POSTGRES.release(self.name, conn)
            except UnboundLocalError:
                self.logger.error(f'{self.name} could not release a connection it never received.')

    def get_time_window_filter(self, query_time):
        # You can't always trust that a set from kernel made up of time window
        # start < _time < end is complete if nearlyequal(_time, now()).
        # Sometimes rows belonging to that set would show up a couple mS after
        # the window had closed and be dropped. Our solution was to truncate sets
        # based on the insert time and now() to provide a buffer.
        TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'

        def fn(row):
            commited = datetime.strptime(row.get('modified')[:26], TIME_FORMAT)
            lag_time = (query_time - commited).total_seconds()
            if lag_time > self.window_size_sec:
                return True
            elif lag_time < -30.0:
                # Sometimes fractional negatives show up. More than 30 seconds is an issue though.
                self.logger.critical(
                    'INVALID LAG INTERVAL: %s. Check time settings on server.' % lag_time)
            _id = row.get('id')
            self.logger.debug('WINDOW EXCLUDE: ID: %s, LAG: %s' % (_id, lag_time))
            return False
        return fn

    def get_db_updates(self):
        modified = '' if not self.offset else self.offset  # "" evals to < all strings
        query = sql.SQL(TopicManager.QUERY_STR).format(
            modified=sql.Literal(modified),
            schema_name=sql.Literal(self.name),
            limit=sql.Literal(self.limit),
            realm=sql.Literal(self.realm)
        )
        query_time = datetime.now()

        try:
            promise = POSTGRES.request_connection(2, self.name)  # Lowest priority
            conn = promise.get()
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(query)
            window_filter = self.get_time_window_filter(query_time)
            return [{key: row[key] for key in row.keys()} for row in cursor if window_filter(row)]
        except psycopg2.OperationalError as pgerr:
            self.logger.critical(
                'Could not access Database to look for updates: %s' % pgerr)
            return []
        finally:
            try:
                POSTGRES.release(self.name, conn)
            except UnboundLocalError:
                self.logger.error(f'{self.name} could not release a connection it never received.')

    def get_topic_size(self):
        query = sql.SQL(TopicManager.COUNT_STR).format(
            schema_name=sql.Literal(self.name),
            realm=sql.Literal(self.realm)
        )
        try:
            promise = POSTGRES.request_connection(0, self.name)  # needs to be quick
            conn = promise.get()
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(query)
            size = [{key: row[key] for key in row.keys()} for row in cursor][0]
            self.logger.debug(f'''Reporting requested size for {self.name} of {size['count']}''')
            return size
        except psycopg2.OperationalError as pgerr:
            self.logger.critical(
                'Could not access db to get topic size: %s' % pgerr)
            return -1
        finally:
            try:
                POSTGRES.release(self.name, conn)
            except UnboundLocalError:
                self.logger.error(f'{self.name} could not release a connection it never received.')

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
            self.logger.error('ERROR %s', [err, msg, kwargs])
        with io.BytesIO() as obj:
            obj.write(msg.value())
            reader = DataFileReader(obj, DatumReader())
            for message in reader:
                _id = message.get('id')
                if err:
                    self.logger.debug('NO-SAVE: %s in topic %s | err %s' %
                                      (_id, self.topic_name, err.name()))
                    self.failed_changes[_id] = err
                else:
                    self.logger.debug('SAVE: %s in topic %s' % (_id, self.topic_name))
                    self.successful_changes.append(_id)

    def update_kafka(self):
        # Main update loop
        # Monitors postgres for changes via TopicManager.updates_available
        # Consumes updates to the Posgres DB via TopicManager.get_db_updates
        # Sends new messages to Kafka
        # Registers message callback (ok or fail) to TopicManager.kafka_callback
        # Waits for all messages to be accepted or timeout in TopicManager.wait_for_kafka
        self.logger.debug(f'Topic {self.name}: Initializing')
        while self.operating_status is TopicStatus.INITIALIZING:
            if self.context.killed:
                return
            self.logger.debug(f'Waiting for topic {self.name} to initialize...')
            self.context.safe_sleep(self.wait_time)
            pass

        while not self.context.killed:
            if self.operating_status is not TopicStatus.NORMAL:
                self.logger.debug(
                    f'Topic {self.name} not updating, status: {self.operating_status}'
                    + f', waiting {self.wait_time}(sec)')
                self.context.safe_sleep(self.wait_time)
                continue

            if not self.context.kafka_available():
                self.logger.debug('Kafka Container not accessible, waiting.')
                self.context.safe_sleep(self.wait_time)
                continue

            self.offset = self.get_offset()
            if not self.updates_available():
                self.logger.debug('No updates')
                self.context.safe_sleep(self.wait_time)
                continue
            try:
                self.logger.debug('Getting Changeset for %s' % self.name)
                self.change_set = {}
                new_rows = self.get_db_updates()
                if not new_rows:
                    self.context.safe_sleep(self.wait_time)
                    continue
                end_offset = new_rows[-1].get('modified')
            except Exception as pge:
                self.logger.error(
                    'Could not get new records from kernel: %s' % pge)
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
                            self.logger.debug(
                                'ENQUEUE MSG TOPIC: %s, ID: %s, MOD: %s' % (
                                    self.name,
                                    _id,
                                    modified
                                ))
                            self.change_set[_id] = row
                            writer.append(msg)
                        else:
                            # Message doesn't have the proper format for the current schema.
                            self.logger.critical(
                                'SCHEMA_MISMATCH:NOT SAVED! TOPIC:%s, ID:%s' % (self.name, _id))

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
                self.logger.error('error in Kafka save: %s' % ke)
                self.logger.error(traceback.format_exc())
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
                self.handle_kafka_errors(
                    change_set_size, all_failed=True, failure_wait_time=failure_wait_time)
                self.clear_changeset()
                self.logger.info(
                    'Changeset not saved; likely broker outage, sleeping worker for %s' % self.name)
                self.context.safe_sleep(failure_wait_time)
                return  # all failed; ignore changeset

            # All changes were saved
            elif len(self.successful_changes) == change_set_size:

                self.logger.debug(
                    'All changes saved ok in topic %s.' % self.name)
                break

            # Remove successful and errored changes
            for _id, err in self.failed_changes.items():
                try:
                    del self.change_set[_id]
                except KeyError:
                    pass  # could have been removed on previous iter
            for _id in self.successful_changes:
                try:
                    del self.change_set[_id]
                except KeyError:
                    pass  # could have been removed on previous iter

            # All changes registered
            if len(self.change_set) == 0:
                break

            sleep(sleep_time)

        # Timeout reached or all messages returned ( and not all failed )

        self.status['last_changeset_status'] = {
            'changes': change_set_size,
            'failed': len(self.failed_changes),
            'succeeded': len(self.successful_changes),
            'timestamp': datetime.now().isoformat()
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
            'timestamp': datetime.now().isoformat()
        }

        if not all_failed:
            # Collect Error types for reporting
            for _id, err in self.failed_changes.items():
                self.logger.critical('PRODUCER_FAILURE: T: %s ID %s , ERR_MSG %s' % (
                    self.name, _id, err.name()))
            dropped_messages = change_set_size - len(self.successful_changes)
            errors['NO_REPLY'] = dropped_messages - len(self.failed_changes)
            last_error_set['failed'] = len(self.failed_changes),
            last_error_set['succeeded'] = len(self.successful_changes),
            last_error_set['outcome'] = 'MSGS_DROPPED : %s' % dropped_messages,

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
            self.logger.debug('Got offset for %s | %s' % (self.name, offset))
            return offset
        else:
            self.logger.debug('Could not get offset for %s it is a new type' % (self.name))
            # No valid offset so return None; query will use empty string which is < any value
            return None

    def set_offset(self, offset):
        # Set a new offset in the database
        new_offset = Offset.update(self.name, offset)
        self.logger.debug('new offset for %s | %s' % (self.name, new_offset))
        self.status['offset'] = new_offset
