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
from datetime import datetime
import enum
from functools import wraps
import io
import json
import logging
import os
import signal
import socket
import spavro.schema
import sys
import traceback

from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient
from flask import Flask, Response, request, jsonify
import gevent
from gevent.pool import Pool
from gevent.pywsgi import WSGIServer
import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor
from spavro.datafile import DataFileWriter, DataFileReader
from spavro.io import DatumWriter, DatumReader
from spavro.io import validate

from producer import db
from producer.db import Offset
from producer.db import KERNEL_DB as POSTGRES
from producer.settings import Settings


class KafkaStatus(enum.Enum):
    SUBMISSION_PENDING = 1
    SUBMISSION_FAILURE = 2
    SUBMISSION_SUCCESS = 3


class ProducerManager(object):
    # Serves status & healthcheck over HTTP
    # Dispatches Signals
    # Keeps track of schemas
    # Spawns a TopicManager for each schema type in Kernel
    # TopicManager registers own eventloop greenlet (update_kafka) with ProducerManager

    SCHEMAS_STR = '''
            SELECT
                ps.id as schemadecorator_id,
                ps.name as schemadecorator_name,
                ps.modified as modified,
                s.name as schema_name,
                s.id as schema_id,
                s.definition as schema_definition,
                s.revision as schema_revision,
                mt.realm as realm
            FROM kernel_schemadecorator ps
            inner join kernel_schema s on ps.schema_id = s.id
            inner join multitenancy_mtinstance mt on ps.project_id = mt.instance_id
            ORDER BY s.modified ASC'''

    def __init__(self, settings):
        self.settings = settings
        # Start Signal Handlers
        self.killed = False
        signal.signal(signal.SIGTERM, self.kill)
        signal.signal(signal.SIGINT, self.kill)
        gevent.signal(signal.SIGTERM, self.kill)
        # Turn on Flask Endpoints
        # Get Auth details from env
        self.admin_name = settings.get('PRODUCER_ADMIN_USER')
        self.admin_password = settings.get('PRODUCER_ADMIN_PW')
        self.serve()
        self.add_endpoints()
        # Initialize Offsetdb
        self.init_db()
        # Clear objects and start
        self.kernel = None
        self.kafka = KafkaStatus.SUBMISSION_PENDING
        self.get_admin_client()
        self.topic_managers = {}
        self.run()

    def get_admin_client(self):
        kafka_settings = {"bootstrap.servers": self.settings.get("kafka_url")}
        if self.settings.get('kafka_security', '').lower() == 'sasl_plaintext':
            # Let Producer use Kafka SU to produce
            self.logger.info(f'Using security protocol: SASL_PLAINTEXT')
            kafka_settings['security.protocol'] = 'SASL_PLAINTEXT'
            kafka_settings['sasl.mechanisms'] = 'SCRAM-SHA-256'
            kafka_settings['sasl.username'] = \
                self.settings.get('KAFKA_SU_USER')
            kafka_settings['sasl.password'] = \
                self.settings.get('KAFKA_SU_PW')
        self.kafka_admin_client = AdminClient(kafka_settings)

    def keep_alive_loop(self):
        # Keeps the server up in case all other threads join at the same time.
        while not self.killed:
            sleep(1)

    def run(self):
        self.threads = []
        self.threads.append(gevent.spawn(self.keep_alive_loop))
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

    # see if kafka's port is available
    def kafka_available(self):
        kafka_ip, kafka_port = self.settings["kafka_url"].split(":")
        kafka_port = int(kafka_port)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((kafka_ip, kafka_port))
        except (InterruptedError,
                ConnectionRefusedError,
                socket.gaierror) as rce:
            self.logger.debug(
                "Could not connect to Kafka on url: %s:%s" % (kafka_ip, kafka_port))
            self.logger.debug("Connection problem: %s" % rce)
            return False
        return True

    # Connect to sqlite
    def init_db(self):
        db.init()
        self.logger.info("OffsetDB initialized")

    # Main Schema Loop
    # Spawns TopicManagers for new schemas, updates schemas for workers on change.
    def check_schemas(self):
        # Checks for schemas in Kernel
        # Creates TopicManagers for found schemas.
        # Updates TopicManager.schema on schema change
        while not self.killed:
            schemas = []
            try:
                schemas = self.get_schemas()
                self.kernel = datetime.now().isoformat()
            except Exception as err:
                self.kernel = None
                self.logger.error(f'no database connection: {err}')
                sleep(1)
                continue
            for schema in schemas:
                _name = schema['schema_name']
                realm = schema['realm']
                schema_name = f'{realm}.{_name}'
                if schema_name not in self.topic_managers.keys():
                    self.logger.info(
                        "New topic connected: %s" % schema_name)
                    self.topic_managers[schema_name] = TopicManager(
                        self, schema, realm)
                else:
                    topic_manager = self.topic_managers[schema_name]
                    if topic_manager.schema_changed(schema):
                        topic_manager.update_schema(schema)
                        self.logger.debug(
                            "Schema %s updated" % schema_name)
                    else:
                        self.logger.debug(
                            "Schema %s unchanged" % schema_name)
            # Time between checks for schema change
            self.safe_sleep(self.settings['sleep_time'])
        self.logger.debug('No longer checking schemas')

    def get_schemas(self):
        name = 'schemas_query'
        query = sql.SQL(ProducerManager.SCHEMAS_STR)
        try:
            # needs to be quick(ish)
            promise = POSTGRES.request_connection(1, name)
            conn = promise.get()
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(query)
            for row in cursor:
                yield {key: row[key] for key in row.keys()}

        except psycopg2.OperationalError as pgerr:
            self.logger.critical(
                'Could not access db to get topic size: %s' % pgerr)
            return -1
        finally:
            try:
                POSTGRES.release(name, conn)
            except UnboundLocalError:
                self.logger.error(
                    f'{name} could not release a'
                    ' connection it never received.'
                )

    # Flask Functions

    def add_endpoints(self):
        # URLS configured here
        self.register('healthcheck', self.request_healthcheck)
        self.register('status', self.request_status)
        self.register('topics', self.request_topics)
        self.register('pause', self.request_pause)
        self.register('resume', self.request_resume)
        self.register('rebuild', self.request_rebuild)

    def register(self, route_name, fn):
        self.app.add_url_rule('/%s' % route_name, route_name, view_func=fn)

    def serve(self):
        self.app = Flask('AetherProducer')  # pylint: disable=invalid-name
        self.logger = self.app.logger
        try:
            handler = self.logger.handlers[0]
        except IndexError:
            handler = logging.StreamHandler()
            self.logger.addHandler(handler)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s [Producer] %(levelname)-8s %(message)s'))
        log_level = logging.getLevelName(self.settings
                                         .get('log_level', 'DEBUG'))
        self.logger.setLevel(log_level)
        # self.logger.setLevel(logging.INFO)
        if log_level == "DEBUG":
            self.app.debug = True
        self.app.config['JSONIFY_PRETTYPRINT_REGULAR'] = self.settings \
            .get('flask_settings', {}) \
            .get('pretty_json_status', False)
        pool_size = self.settings \
            .get('flask_settings', {}) \
            .get('max_connections', 3)
        server_ip = self.settings \
            .get('server_ip', "")
        server_port = int(self.settings
                          .get('server_port', 9005))
        self.worker_pool = Pool(pool_size)
        self.http = WSGIServer(
            (server_ip, server_port),
            self.app.wsgi_app, spawn=self.worker_pool
        )
        self.http.start()

    # Basic Auth implementation

    def check_auth(self, username, password):
        return username == self.admin_name and password == self.admin_password

    def request_authentication(self):
        return Response('Bad Credentials', 401,
                        {'WWW-Authenticate': 'Basic realm="Login Required"'})

    def requires_auth(f):
        @wraps(f)
        def decorated(self, *args, **kwargs):
            auth = request.authorization
            if not auth or not self.check_auth(auth.username, auth.password):
                return self.request_authentication()
            return f(self, *args, **kwargs)
        return decorated

    # Exposed Request Endpoints

    def request_healthcheck(self):
        with self.app.app_context():
            return Response({"healthy": True})

    @requires_auth
    def request_status(self):
        status = {
            "kernel_connected": self.kernel is not None,  # This is a real object
            "kafka_container_accessible": self.kafka_available(),
            # This is just a status flag
            "kafka_submission_status": str(self.kafka),
            "topics": {k: v.get_status() for k, v in self.topic_managers.items()}
        }
        with self.app.app_context():
            return jsonify(**status)

    @requires_auth
    def request_topics(self):
        if not self.topic_managers:
            return Response({})
        status = {k: v.get_topic_size() for k, v in self.topic_managers.items()}
        with self.app.app_context():
            return jsonify(**status)

    # Topic Command API

    @requires_auth
    def request_pause(self):
        return self.handle_topic_command(request, TopicStatus.PAUSED)

    @requires_auth
    def request_resume(self):
        return self.handle_topic_command(request, TopicStatus.NORMAL)

    @requires_auth
    def request_rebuild(self):
        return self.handle_topic_command(request, TopicStatus.REBUILDING)

    def handle_topic_command(self, request, status):
        topic = request.args.get('topic')
        if not topic:
            return Response(f'A topic must be specified', 422)
        if not self.topic_managers.get(topic):
            return Response(f'Bad topic name {topic}', 422)
        manager = self.topic_managers[topic]
        if status is TopicStatus.PAUSED:
            fn = manager.pause
        if status is TopicStatus.NORMAL:
            fn = manager.resume
        if status is TopicStatus.REBUILDING:
            fn = manager.rebuild
        try:
            res = fn()
            if not res:
                return Response(f'Operation failed on {topic}', 500)
            return Response(f'Success for status {status} on {topic}', 200)
        except Exception as err:
            return Response(f'Operation failed on {topic} with: {err}', 500)


class TopicStatus(enum.Enum):
    PAUSED = 1  # Paused
    LOCKED = 2  # Paused by system and non-resumable via API until sys unlock
    REBUILDING = 3  # Topic is being rebuilt
    NORMAL = 4  # Topic is operating normally


class TopicManager(object):

    # Creates a long running job on TopicManager.update_kafka

    # Changes detection query
    NEW_STR = '''
        SELECT
            e.id,
            e.modified
        FROM kernel_entity e
        inner join kernel_schemadecorator sd on e.schemadecorator_id = sd.id
        inner join kernel_schema s on sd.schema_id = s.id
        inner join multitenancy_mtinstance mt on sd.project_id = mt.instance_id
        WHERE e.modified > {modified}
        AND s.name = {schema_name}
        AND mt.realm = {realm}
        LIMIT 1; '''

    # Count how many unique (controlled by kernel) messages should currently be in this topic
    COUNT_STR = '''
            SELECT
                count(e.id)
            FROM kernel_entity e
            inner join kernel_schemadecorator sd on e.schemadecorator_id = sd.id
            inner join kernel_schema s on sd.schema_id = s.id
            inner join multitenancy_mtinstance mt on sd.project_id = mt.instance_id
            WHERE s.name = {schema_name}
            AND mt.realm = {realm};
    '''

    # Changes pull query
    QUERY_STR = '''
            SELECT
                e.id,
                e.revision,
                e.payload,
                e.modified,
                e.status,
                sd.id as schema_decorator_id,
                sd.name as schema_decorator_name,
                s.name as schema_name,
                s.id as schema_id,
                s.revision as schema_revision
            FROM kernel_entity e
            inner join kernel_schemadecorator sd on e.schemadecorator_id = sd.id
            inner join kernel_schema s on sd.schema_id = s.id
            inner join multitenancy_mtinstance mt on sd.project_id = mt.instance_id
            WHERE e.modified > {modified}
            AND mt.realm = {realm}
            AND s.name = {schema_name}
            ORDER BY e.modified ASC
            LIMIT {limit};
        '''

    def __init__(self, server_handler, schema, realm):
        self.context = server_handler
        self.logger = self.context.logger
        self.name = schema['schema_name']
        self.realm = realm
        self.offset = ""
        self.operating_status = TopicStatus.NORMAL
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
        self.pg_creds = {key: self.context.settings.get(
            "postgres_%s" % key) for key in pg_requires}
        self.kafka_failure_wait_time = self.context.settings.get(
            'kafka_failure_wait_time', 10)
        try:
            topic_base = self.context.settings \
                .get('topic_settings', {}) \
                .get('name_modifier', "%s") \
                % self.name
            self.topic_name = f'{self.realm}.{topic_base}'
        except Exception:  # Bad Name
            self.logger.critical(("invalid name_modifier using topic name for topic: %s."
                                  " Update configuration for"
                                  " topic_settings.name_modifier") % self.name)
            # This is a failure which could cause topics to collide. We'll kill the producer
            # so the configuration can be updated.
            sys.exit(1)
        self.update_schema(schema)
        self.get_producer()
        # Spawn worker and give to pool.
        self.context.threads.append(gevent.spawn(self.update_kafka))

    def get_producer(self):
        kafka_settings = self.context.settings.get('kafka_settings')
        # apply setting from root config to be able to use env variables
        kafka_settings["bootstrap.servers"] = self.context.settings.get(
            "kafka_url")
        self.kafka_settings = kafka_settings
        # check for SASL
        if self.context.settings.get('kafka_security', '').lower() == 'sasl_plaintext':
            # Let Producer use Kafka SU to produce
            self.logger.info(f'Using security protocol: SASL_PLAINTEXT')
            self.kafka_settings['security.protocol'] = 'SASL_PLAINTEXT'
            self.kafka_settings['sasl.mechanisms'] = 'SCRAM-SHA-256'
            self.kafka_settings['sasl.username'] = \
                self.context.settings.get('KAFKA_SU_USER')
            self.kafka_settings['sasl.password'] = \
                self.context.settings.get('KAFKA_SU_PW')

        self.context.app.logger.critical(self.kafka_settings)
        self.producer = Producer(**self.kafka_settings)

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
                         + f' {self.wait_time *1.5}(sec) for inflight ops to resolve')
        self.context.safe_sleep(int(self.wait_time * 1.5))
        self.logger.info(f'{tag} Deleting Topic')
        self.producer = None
        ok = self.delete_this_topic()
        if not ok:
            self.logger.critical(f'{tag} FAILED. Topic will not resume.')
            self.operating_status = TopicStatus.LOCKED
            return
        self.logger.warn(f'{tag} Resetting Offset.')
        self.set_offset("")
        self.logger.info(f'{tag} Rebuilding Topic Producer')
        self.producer = Producer(**self.kafka_settings)
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

        modified = "" if not self.offset else self.offset  # "" evals to < all strings
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

                self.producer.poll(0)
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
            self.logger.debug("Got offset for %s | %s" %
                              (self.name, offset))
            return offset
        else:
            self.logger.debug(
                'Could not get offset for %s it is a new type' % (self.name))
            # No valid offset so return None; query will use empty string which is < any value
            return None

    def set_offset(self, offset):
        # Set a new offset in the database
        new_offset = Offset.update(self.name, offset)
        self.logger.debug("new offset for %s | %s" %
                          (self.name, new_offset))
        self.status['offset'] = new_offset


def main():
    file_path = os.environ.get('PRODUCER_SETTINGS_FILE')
    settings = Settings(file_path)
    ProducerManager(settings)
