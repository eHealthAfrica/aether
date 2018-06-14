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
from collections import UserDict
from contextlib import contextmanager
from datetime import datetime
import gevent
from gevent.pool import Pool
import io
import json
import logging
import os
import psycopg2
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


class Settings(UserDict):
    # A container for our settings
    def __init__(self, test=False):
        SETTINGS_FILE = "%s/settings.json" % FILE_PATH
        TEST_SETTINGS_FILE = "%s/test_settings.json" % FILE_PATH
        self.data = {}
        if test:
            self.load(TEST_SETTINGS_FILE)
        else:
            self.load(SETTINGS_FILE)

    def load(self, path):
        with open(path) as f:
            obj = json.load(f)
            for k in obj:
                self.data[k] = obj.get(k)
            self.data['offset_path'] = "%s/%s" % (
                FILE_PATH, self.data['offset_file'])


class KernelHandler(object):
    # Context for Kernel, which nulls kernel for reconnection if an error occurs
    # Errors of type ignored_exceptions are logged but don't null kernel
    def __init__(self, handler, ignored_exceptions=None):
        self.handler = handler
        self.log = self.handler.logger
        if ignored_exceptions is not None and isinstance(ignored_exceptions, list) is not True:
            self.ignored_exceptions = [ignored_exceptions]
        elif ignored_exceptions is not None:
            self.ignored_exceptions = ignored_exceptions
        else:
            self.ignored_exceptions = []

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, traceback):
        if exc_type:
            if exc_type in self.ignored_exceptions:
                return True
            self.handler.kernel = None
            self.log.error("Lost Kernel Connection: %s" % exc_type)
            return True
        return True


class ServerHandler(object):
    # Serves status & healthcheck over HTTP
    # Dispatches Signals
    # Keeps track of schemas
    # Spawns/ Manages all Topics

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
        self.schema_handlers = {}
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
        gevent.joinall(self.threads)

    def update_schema(self, name):
        pass

    def kill(self, *args, **kwargs):
        # Stops HTTP service and flips stop switch, which is read by greenlets
        self.app.logger.warn('Shutting down gracefully')
        self.http.stop()
        self.http.close()
        self.worker_pool.kill()
        self.killed = True

    def safe_sleep(self, dur):
        # keeps shutdown time low
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
        self.logger.info('Connecting to Aether...')
        self.kernel = None
        while not self.killed:
            try:
                if not self.kernel:
                    with KernelHandler(self, ignored_exceptions=[MaxRetryError, ConnectionError]):
                        self.kernel = KernelClient(
                            url=self.settings['kernel_url'],
                            **self.settings['kernel_credentials']
                        )
                        self.logger.info('Connected to Aether.')
                        continue
                    self.safe_sleep(self.settings['start_delay'])
                else:
                    self.safe_sleep(1)
            except Exception as e:
                self.logger.info('No Aether connection...')
                self.safe_sleep(self.settings['start_delay'])

        self.logger.debug('No longer attempting to connect to Aether')

    # Main Kafka / Schema Loop
    def check_schemas(self):
        # Checks for schemas in Kernel
        # Creates SchemaHandlers for found schemas.
        # Updates SchemaHandler.schema on schema change
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
                    if not schema.name in self.schema_handlers.keys():
                        self.logger.info(
                            "New topic connected: %s" % schema.name)
                        self.schema_handlers[schema.name] = SchemaHandler(
                            self, schema)
                    else:
                        res = self.schema_handlers[schema.name]
                        if res.schema_obj != res.parse_schema(schema):
                            res.update_schema(schema)
                            self.logger.info("Schema %s updated" % schema.name)
                        else:
                            self.logger.debug("Schema %s unchanged" % schema.name)
                # Time between checks for schema change
                self.safe_sleep(10)
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
        self.app.debug = True
        pool_size = self.settings.get(
            'flask_settings', {}).get('max_connections', 1)
        port = self.settings.get('flask_settings', {}).get('port', 5005)
        self.worker_pool = Pool(pool_size)
        self.http = WSGIServer(
            ('', port), self.app.wsgi_app, spawn=self.worker_pool)
        self.http.start()

    # Exposed Request Endpoints

    def request_healthcheck(self):
        with self.app.app_context():
            return Response({"healthy": True})

    def request_status(self):
        status = {
                "kernel": self.kernel is not None,  # This is a real object
                "kafka": self.kafka is not False,   # This is just a status flag
                "topics": {k: v.get_status() for k, v in self.schema_handlers.items()}
            }
        with self.app.app_context():
            return jsonify(status)


class SchemaHandler(object):

    # Changes detection
    NEW_STR = '''
        SELECT
            e.id,
            e.modified
        FROM kernel_entity e
        inner join kernel_projectschema ps on e.projectschema_id = ps.id
        inner join kernel_schema s on ps.schema_id = s.id
        WHERE e.modified > '%s'
        AND s.name = '%s'
        LIMIT 1; '''

    # Changes query
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
            WHERE e.modified > '%s'
            AND s.name = '%s'
            ORDER BY e.modified ASC
            LIMIT %d;
        '''

    def __init__(self, server_handler, schema):
        self.context = server_handler
        self.logger = self.context.logger
        self.name = schema.name
        self.modified = ""
        self.limit = self.context.settings.get('postgres_pull_limit', 100)
        self.status = {
            "last_errors_set": {},
            "last_changeset_status": {}
        }
        self.change_set = {}
        self.successful_changes = []
        self.failed_changes = {}
        self.pg_creds = self.context.settings.get('postgres_connection_info')
        self.kafka_failure_wait_time = self.context.settings.get('kafka_failure_wait_time', 10)
        try:
            self.topic_name = self.context.settings \
                .get('topic_settings', {}) \
                .get('name_modifier', "%s") \
                % self.name
        except Exception as err:  # Bad Name
            self.topic_name = self.name
        self.update_schema(schema)
        self.producer = Producer(**self.context.settings.get('kafka_settings'))
        # Spawn worker and give to pool.
        self.context.threads.append(gevent.spawn(self.update_kafka))

    def updates_available(self):
        query = SchemaHandler.NEW_STR % (self.modified, self.name)
        with psycopg2.connect(**self.pg_creds) as conn:
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(query)
            return sum([1 for i in cursor]) > 0

    def get_db_updates(self):
        query = SchemaHandler.QUERY_STR % (
            self.modified, self.name, self.limit)
        with psycopg2.connect(**self.pg_creds) as conn:
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(query)
            return [{key: row[key] for key in row.keys()} for row in cursor]

    def update_schema(self, schema_obj):
        self.schema_obj = self.parse_schema(schema_obj)
        self.schema = spavro.schema.parse(json.dumps(self.schema_obj))

    def parse_schema(self, schema_obj):
        return ast.literal_eval(str(schema_obj.definition))

    def get_status(self):
        # Updates inflight status and returns to Flask called
        self.status['inflight'] = [i for i in self.change_set.keys()]
        return self.status

    # Callback function registered with Kafka Producer to acknowledge receipt
    def kafka_callback(self, err=None, msg=None, _=None, **kwargs):
        try:
            obj = io.BytesIO()
            if err:
                obj.write(msg.value())
                reader = DataFileReader(obj, DatumReader())
                for x, message in enumerate(reader):
                    _id = message.get("id")
                    self.logger.info("NO-SAVE: %s in topic %s | err %s" %
                                      (_id, self.topic_name, err.name()))
                    self.failed_changes[_id] = err
            else:
                obj.write(msg.value())
                reader = DataFileReader(obj, DatumReader())
                for x, message in enumerate(reader):
                    _id = message.get("id")
                    self.logger.debug("SAVE: %s in topic %s" %
                                      (_id, self.topic_name))
                    self.successful_changes.append(_id)
        except Exception as error:
            self.logger.debug('ERROR %s ', [error, _, msg, err, kwargs])
        finally:
            obj.close()

    def update_kafka(self):
        # Main update loop
        # Takes records from PostGres
        # Gives them to Kafka
        # Kicks off wait for receipt acknowledgement before saving new offset
        while not self.context.killed:

            self.modified = self.get_offset()
            if not self.updates_available():
                self.logger.debug('No updates')
                sleep(1)
                continue
            try:
                self.logger.debug("Getting Changeset for %s" % self.name)
                self.change_set = {}
                new_rows = self.get_db_updates()
                end_offset = new_rows[-1].get('modified')

                bytes_writer = io.BytesIO()
                writer = DataFileWriter(
                    bytes_writer, DatumWriter(), self.schema, codec='deflate')

                for row in new_rows:
                    _id = row['id']
                    msg = row.get("payload")
                    self.change_set[_id] = row
                    writer.append(msg)

                writer.flush()
                raw_bytes = bytes_writer.getvalue()
                writer.close()

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
                sleep(1)

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

                self.logger.debug('All changes saved ok.')
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

            self.context.safe_sleep(sleep_time)

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
                    "outcome" : "RETRY",
                    "timestamp": datetime.now().isoformat()
                    }

        if not all_failed:
            # Collect Error types for reporting
            for _id, err in self.failed_changes.items():
                self.logger.error('KernelHandlerFAILURE: T: %s ID %s , ERR_MSG %s' % (
                    self.name, _id, err.name()))
            dropped_messages = change_set_size - len(self.successful_changes)
            errors["NO_REPLY"] = dropped_messages -len(self.failed_changes)
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
        try:
            offset = Offset.get_offset(self.name)
            if offset:
                self.logger.debug("Got offset for %s | %s" % (self.name, offset.offset_value))
                return offset.offset_value
            else:
                raise ValueError('No entry for %s' % self.name)
        except Exception as err:
            self.logger.error('Could not get offset for %s it is a new type' % (self.name))
            return "" # No valid offset so return empty string which is < any value

    def set_offset(self, offset):
        # Set a new offset in the database
        new_offset = Offset.update(self.name, offset)
        if not new_offset:
            self.logger.info('Creating new offset entry for %s' % self.name)
            Offset.create(schema_name=self.name, offset_value=offset)
        else:
            self.logger.debug("new offset for %s | %s" %
                              (self.name, new_offset.offset_value))
        self.status['offset'] = new_offset.offset_value


def main(test=False):
    settings = Settings(test=test)
    handler = ServerHandler(settings)
