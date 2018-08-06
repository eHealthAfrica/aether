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

from gevent import monkey, sleep
# need to patch sockets to make requests async
monkey.patch_all()
import psycogreen.gevent
psycogreen.gevent.patch_psycopg()

import ast
from contextlib import contextmanager
from datetime import datetime
import gevent
from gevent.pool import Pool
import io
import json
import logging
import os
import psycopg2
from psycopg2 import sql
import signal
import spavro.schema
import sys
import traceback

from aether.client import KernelClient
from flask import Flask, Response, request, abort, jsonify
from gevent.pywsgi import WSGIServer
from confluent_kafka import Producer, Consumer, KafkaException
from psycopg2.extras import DictCursor
from requests.exceptions import ConnectionError
from spavro.datafile import DataFileWriter, DataFileReader
from spavro.io import DatumWriter, DatumReader
from spavro.io import validate
from urllib3.exceptions import MaxRetryError

from producer import db
from producer.db import Offset

FILE_PATH = os.path.dirname(os.path.realpath(__file__))


class Settings(dict):
    # A container for our settings
    def __init__(self, file_path=None):
        self.load(file_path)

    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def __getitem__(self, key):
        result = os.environ.get(key.upper())
        if result is None:
            result = super().__getitem__(key)

        return result

    def load(self, path):
        with open(path) as f:
            obj = json.load(f)
            for k in obj:
                self[k] = obj.get(k)


class KernelHandler(object):
    # Context for Kernel, which nulls kernel for reconnection if an error occurs
    # Errors of type ignored_exceptions are logged but don't null kernel
    def __init__(self, handler, ignored_exceptions=None):
        self.handler = handler
        self.log = self.handler.logger
        self.ignored_exceptions = ignored_exceptions

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, traceback):
        if exc_type:
            if self.ignored_exceptions and exc_type in self.ignored_exceptions:
                return True
            self.handler.kernel = None
            self.log.info("Kernel Connection Failed: %s" % exc_type)
            return False
        return True


class ProducerManager(object):
    # Serves status & healthcheck over HTTP
    # Dispatches Signals
    # Keeps track of schemas
    # Spawns a TopicManager for each schema type in Kernel
    # TopicManager registers own eventloop greenlet (update_kafka) with ProducerManager

    def __init__(self, settings):
        self.settings = settings
        # Start Signal Handlers
        self.killed = False
        signal.signal(signal.SIGTERM, self.kill)
        signal.signal(signal.SIGINT, self.kill)
        gevent.signal(signal.SIGTERM, self.kill)
        # Turn on Flask Endpoints
        self.serve()
        self.add_endpoints()
        # Initialize Offsetdb
        self.init_db()
        # Clear objects and start
        self.kernel = None
        self.kafka = False
        self.topic_managers = {}
        self.run()

    def keep_alive_loop(self):
        # Keeps the server up in case all other threads join at the same time.
        while not self.killed:
            sleep(1)

    def run(self):
        self.threads = []
        self.threads.append(gevent.spawn(self.keep_alive_loop))
        self.threads.append(gevent.spawn(self.connect_aether))
        self.threads.append(gevent.spawn(self.check_schemas))
        # Also going into this greenlet pool:
        # Each TopicManager.update_kafka() from TopicManager.init
        gevent.joinall(self.threads)

    def kill(self, *args, **kwargs):
        # Stops HTTP service and flips stop switch, which is read by greenlets
        self.app.logger.warn('Shutting down gracefully')
        self.http.stop()
        self.http.close()
        self.worker_pool.kill()
        self.killed = True  # Flag checked by spawned TopicManagers to stop themselves

    def safe_sleep(self, dur):
        # keeps shutdown time low by yielding during sleep and checking if killed.
        for x in range(dur):
            if not self.killed:
                sleep(1)

    # Connectivity

    # Connect to sqlite
    def init_db(self):
        url = self.settings.get('offset_db_url')
        db.init(url)
        self.logger.info("OffsetDB initialized at %s" % url)

    # Maintain Aether Connection
    def connect_aether(self):
        self.kernel = None
        while not self.killed:
            errored = False
            try:
                if not self.kernel:
                    self.logger.info('Connecting to Aether...')
                    with KernelHandler(self):
                        self.kernel = KernelClient(
                            url=self.settings['kernel_url'],
                            username=self.settings['kernel_admin_username'],
                            password=self.settings['kernel_admin_password'],
                        )
                        self.logger.info('Connected to Aether.')
                        continue
                self.safe_sleep(self.settings['start_delay'])

            except ConnectionError as ce:
                errored = True
                self.logger.debug(ce)
            except MaxRetryError as mre:
                errored = True
                self.logger.debug(mre)
            except Exception as err:
                errored = True
                self.logger.debug(err)

            if errored:
                self.logger.info('No Aether connection...')
                self.safe_sleep(self.settings['start_delay'])
            errored = False

        self.logger.debug('No longer attempting to connect to Aether')

    # Main Schema Loop
    # Spawns TopicManagers for new schemas, updates schemas for workers on change.
    def check_schemas(self):
        # Checks for schemas in Kernel
        # Creates TopicManagers for found schemas.
        # Updates TopicManager.schema on schema change
        while not self.killed:
            if not self.kernel:
                sleep(1)
            else:
                schemas = []
                with KernelHandler(self):
                    self.kernel.refresh()
                    schemas = [
                        schema for schema in self.kernel.Resource.Schema]
                for schema in schemas:
                    if not schema.name in self.topic_managers.keys():
                        self.logger.info(
                            "New topic connected: %s" % schema.name)
                        self.topic_managers[schema.name] = TopicManager(
                            self, schema)
                    else:
                        topic_manager = self.topic_managers[schema.name]
                        if topic_manager.schema_changed(schema):
                            topic_manager.update_schema(schema)
                            self.logger.debug(
                                "Schema %s updated" % schema.name)
                        else:
                            self.logger.debug(
                                "Schema %s unchanged" % schema.name)
                # Time between checks for schema change
                self.safe_sleep(self.settings['sleep_time'])
        self.logger.debug('No longer checking schemas')

    # Flask Functions

    def add_endpoints(self):
        # URLS configured here
        self.register('healthcheck', self.request_healthcheck)
        self.register('status', self.request_status)

    def register(self, route_name, fn):
        self.app.add_url_rule('/%s' % route_name, route_name, view_func=fn)

    def serve(self):
        self.app = Flask(__name__)  # pylint: disable=invalid-name
        self.logger = self.app.logger
        log_level = logging.getLevelName(
            self.settings.get('log_level', 'DEBUG'))
        self.logger.setLevel(log_level)
        if log_level is "DEBUG":
            self.app.debug = True
        self.app.config['JSONIFY_PRETTYPRINT_REGULAR'] = self.settings.get(
            'flask_settings', {}).get('pretty_json_status', False)
        pool_size = self.settings.get(
            'flask_settings', {}).get('max_connections', 1)
        server_ip = self.settings.get('server_ip', "")
        server_port = int(self.settings.get('server_port', 9005))
        self.worker_pool = Pool(pool_size)
        self.http = WSGIServer(
            (server_ip, server_port),
            self.app.wsgi_app, spawn=self.worker_pool
        )
        self.http.start()

    # Exposed Request Endpoints

    def request_healthcheck(self):
        with self.app.app_context():
            return Response({"healthy": True})

    def request_status(self):
        status = {
            "kernel": self.kernel is not None,  # This is a real object
            "kafka": self.kafka is not False,   # This is just a status flag
            "topics": {k: v.get_status() for k, v in self.topic_managers.items()}
        }
        with self.app.app_context():
            return jsonify(**status)


class TopicManager(object):

    # Creates a long running job on TopicManager.update_kafka

    # Changes detection query
    NEW_STR = '''
        SELECT
            e.id,
            e.modified
        FROM kernel_entity e
        inner join kernel_projectschema ps on e.projectschema_id = ps.id
        inner join kernel_schema s on ps.schema_id = s.id
        WHERE e.modified > {modified}
        AND s.name = {schema_name}
        LIMIT 1; '''

    # Changes pull query
    QUERY_STR = '''
            SELECT
                e.id,
                e.revision,
                e.payload,
                e.modified,
                e.status,
                ps.id as project_schema_id,
                ps.name as project_schema_name,
                s.name as schema_name,
                s.id as schema_id,
                s.revision as schema_revision
            FROM kernel_entity e
            inner join kernel_projectschema ps on e.projectschema_id = ps.id
            inner join kernel_schema s on ps.schema_id = s.id
            WHERE e.modified > {modified}
            AND s.name = {schema_name}
            ORDER BY e.modified ASC
            LIMIT {limit};
        '''

    def __init__(self, server_handler, schema):
        self.context = server_handler
        self.logger = self.context.logger
        self.name = schema.name
        self.offset = ""
        self.limit = self.context.settings.get('postgres_pull_limit', 100)
        self.status = {
            "last_errors_set": {},
            "last_changeset_status": {}
        }
        self.change_set = {}
        self.successful_changes = []
        self.failed_changes = {}
        self.wait_time = self.context.settings.get('sleep_time', 2)
        self.window_size_sec = self.context.settings.get('window_size_sec', 3)
        pg_requires = ['user', 'dbname', 'port', 'host', 'password']
        self.pg_creds = {key: self.context.settings.get("postgres_%s" % key) for key in pg_requires}
        self.kafka_failure_wait_time = self.context.settings.get(
            'kafka_failure_wait_time', 10)
        try:
            self.topic_name = self.context.settings \
                .get('topic_settings', {}) \
                .get('name_modifier', "%s") \
                % self.name
        except Exception as err:  # Bad Name
            self.logger.critical(("invalid name_modifier using topic name for topic: %s."
                                  " Update configuration for"
                                  " topic_settings.name_modifier") % self.name)
            # This is a failure which could cause topics to collide. We'll kill the producer
            # so the configuration can be updated.
            sys.exit(1)
        self.update_schema(schema)
        kafka_settings = self.context.settings.get('kafka_settings')
        # apply setting from root config to be able to use env variables
        kafka_settings["bootstrap.servers"] = self.context.settings.get("kafka_bootstrap_servers")
        self.producer = Producer(**kafka_settings)
        # Spawn worker and give to pool.
        self.context.threads.append(gevent.spawn(self.update_kafka))

    def updates_available(self):

        modified = "" if not self.offset else self.offset  # "" evals to < all strings
        query = sql.SQL(TopicManager.NEW_STR).format(
            modified=sql.Literal(modified),
            schema_name=sql.Literal(self.name),
        )
        with psycopg2.connect(**self.pg_creds) as conn:
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(query)
            return sum([1 for i in cursor]) > 0

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
                    "INVALID LAG INTERVAL: %s. Check time settings on server." % lag_time)
            _id = row.get('id')
            self.logger.debug("WINDOW EXCLUDE: ID: %s, LAG: %s" %
                              (_id, lag_time))
            return False
        return fn

    def get_db_updates(self):
        modified = "" if not self.offset else self.offset  # "" evals to < all strings
        query = sql.SQL(TopicManager.QUERY_STR).format(
            modified=sql.Literal(modified),
            schema_name=sql.Literal(self.name),
            limit=sql.Literal(self.limit),
        )
        query_time = datetime.now()
        with psycopg2.connect(**self.pg_creds) as conn:
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(query)
            # Since this cursor is of limited size, we keep it in memory instead of
            # returning an iterator to free up the DB resource
            window_filter = self.get_time_window_filter(query_time)
            return [{key: row[key] for key in row.keys()} for row in cursor if window_filter(row)]

    def update_schema(self, schema_obj):
        self.schema_obj = self.parse_schema(schema_obj)
        self.schema = spavro.schema.parse(json.dumps(self.schema_obj))

    def parse_schema(self, schema_obj):
        # We split this method from update_schema because schema_obj as it is can not
        # be compared for differences. literal_eval fixes this. As such, this is used
        # by the schema_changed() method.
        return ast.literal_eval(str(schema_obj.definition))

    def schema_changed(self, schema_candidate):
        # for use by ProducerManager.check_schemas()
        return self.parse_schema(schema_candidate) != self.schema_obj

    def get_status(self):
        # Updates inflight status and returns to Flask called
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
                _id = message.get("id")
                if err:
                    self.logger.debug("NO-SAVE: %s in topic %s | err %s" %
                                      (_id, self.topic_name, err.name()))
                    self.failed_changes[_id] = err
                else:
                    self.logger.debug("SAVE: %s in topic %s" %
                                      (_id, self.topic_name))
                    self.successful_changes.append(_id)

    def update_kafka(self):
        # Main update loop
        # Monitors postgres for changes via TopicManager.updates_available
        # Consumes updates to the Posgres DB via TopicManager.get_db_updates
        # Sends new messages to Kafka
        # Registers message callback (ok or fail) to TopicManager.kafka_callback
        # Waits for all messages to be accepted or timeout in TopicManager.wait_for_kafka

        while not self.context.killed:

            self.offset = self.get_offset()
            if not self.updates_available():
                self.logger.debug('No updates')
                self.context.safe_sleep(self.wait_time)
                continue
            try:
                self.logger.debug("Getting Changeset for %s" % self.name)
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
                        msg = row.get("payload")
                        modified = row.get("modified")
                        if validate(self.schema, msg):
                            # Message validates against current schema
                            self.logger.debug(
                                "ENQUEUE MSG TOPIC: %s, ID: %s, MOD: %s" % (
                                    self.name,
                                    _id,
                                    modified
                                ))
                            self.change_set[_id] = row
                            writer.append(msg)
                        else:
                            # Message doesn't have the proper format for the current schema.
                            self.logger.critical(
                                "SCHEMA_MISMATCH:NOT SAVED! TOPIC:%s, ID:%s" % (self.name, _id))

                    writer.flush()
                    raw_bytes = bytes_writer.getvalue()

                self.producer.produce(
                    self.topic_name,
                    raw_bytes,
                    callback=self.kafka_callback
                )
                self.producer.flush()
                self.wait_for_kafka(
                    end_offset, failure_wait_time=self.kafka_failure_wait_time)

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
                except KeyError as ke:
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

        self.status["last_changeset_status"] = {
            "changes": change_set_size,
            "failed": len(self.failed_changes),
            "succeeded": len(self.successful_changes),
            "timestamp": datetime.now().isoformat()
        }
        if errors:
            self.handle_kafka_errors(change_set_size, all_failed=False)
        self.clear_changeset()
        # Once we're satisfied, we set the new offset past the processed messages
        self.context.kafka = True
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
            "changes": change_set_size,
            "errors": errors,
            "outcome": "RETRY",
            "timestamp": datetime.now().isoformat()
        }

        if not all_failed:
            # Collect Error types for reporting
            for _id, err in self.failed_changes.items():
                self.logger.critical('PRODUCER_FAILURE: T: %s ID %s , ERR_MSG %s' % (
                    self.name, _id, err.name()))
            dropped_messages = change_set_size - len(self.successful_changes)
            errors["NO_REPLY"] = dropped_messages - len(self.failed_changes)
            last_error_set["failed"] = len(self.failed_changes),
            last_error_set["succeeded"] = len(self.successful_changes),
            last_error_set["outcome"] = "MSGS_DROPPED : %s" % dropped_messages,

        self.status["last_errors_set"] = last_error_set
        if all_failed:
            self.context.kafka = False
        return

    def clear_changeset(self):
        self.failed_changes = {}
        self.successful_changes = []
        self.change_set = {}

    def get_offset(self):
        # Get current offset from Database
        offset = Offset.get_offset(self.name)
        if offset:
            self.logger.debug("Got offset for %s | %s" %
                              (self.name, offset.offset_value))
            return offset.offset_value
        else:
            self.logger.debug(
                'Could not get offset for %s it is a new type' % (self.name))
            # No valid offset so return None; query will use empty string which is < any value
            return None

    def set_offset(self, offset):
        # Set a new offset in the database
        new_offset = Offset.update(self.name, offset)
        self.logger.debug("new offset for %s | %s" %
                          (self.name, new_offset.offset_value))
        self.status['offset'] = new_offset.offset_value


def main(file_path=None):
    settings = Settings(file_path)
    handler = ProducerManager(settings)
