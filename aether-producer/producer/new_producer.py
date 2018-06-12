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

from collections import UserDict
from contextlib import contextmanager
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
from traceback import format_exc

from aether.client import KernelClient
from flask import Flask, Response, request, abort, jsonify
from gevent.pywsgi import WSGIServer
from confluent_kafka import Producer, Consumer, KafkaException
from psycopg2.extras import DictCursor
from requests.exceptions import ConnectionError
from spavro.datafile import DataFileWriter
from spavro.io import DatumWriter
from spavro.io import validate
from urllib3.exceptions import MaxRetryError

from producer import db
from producer.db import Offset

FILE_PATH = os.path.dirname(os.path.realpath(__file__))

class Settings(UserDict):

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
            self.data['offset_path'] = "%s/%s" % (FILE_PATH, self.data['offset_file'])


class kHandler(object):
    # Context for Kernel, which nulls kernel for reconnection if an error occurs
    # We can catch some error types if required for just logging
    # Errors in classes ignored_exceptions are logged but don't null kernel
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
            self.log.error("Lost Aether Connection: %s" % exc_type)
            return True
        return True


class ServerHandler(object):
    def __init__(self, settings):
        self.settings = settings
        #Start Signal Handlers
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
        self.schema_handlers = {}
        self.run()

    def keep_alive_loop(self):
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
        self.app.logger.warn('Shutting down gracefully')
        self.http.stop()
        self.http.close()
        self.worker_pool.kill()
        self.killed = True


    # Connectivity

    def init_db(self):
        url = self.settings.get('offset_db_url')
        db.init(url)
        self.logger.info("OffsetDB initialized at %s" % url)

    def connect_aether(self):
        self.logger.info('Connecting to Aether...')
        self.kernel = None
        while not self.killed:
            try:
                if not self.kernel:
                    with kHandler(self, ignored_exceptions=[MaxRetryError, ConnectionError]):
                        self.kernel = KernelClient(
                            url=self.settings['kernel_url'],
                            **self.settings['kernel_credentials']
                        )
                        self.logger.info('Connected to Aether.')
                        continue
                    sleep(self.settings['start_delay'])
                else:
                    sleep(self.settings['start_delay'])
            except Exception as e:
                self.logger.info('No Aether connection...')
                sleep(self.settings['start_delay'])

        self.logger.debug('No longer attempting to connect to Aether')

    def check_schemas(self):
        while not self.killed:
            if not self.kernel:
                sleep(1)
            else:
                schemas = []
                with kHandler(self):
                    self.kernel.refresh()
                    schemas = [schema for schema in self.kernel.Resource.Schema]
                for schema in schemas:
                    if not schema.name in self.schema_handlers.keys():
                        self.logger.info("New topic connected: %s" % schema.name)
                        self.schema_handlers[schema.name] = SchemaHandler(self, schema)
                    else:
                        print("old %s" % schema.name)
                for x in range(10):
                    if not self.killed:
                        sleep(1)
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
        log_level = logging.getLevelName(self.settings.get('log_level', 'DEBUG'))
        self.logger.setLevel(log_level)
        self.app.debug = True
        pool_size = self.settings.get('flask_settings', {}).get('max_connections', 1)
        port = self.settings.get('flask_settings', {}).get('port', 5005)
        self.worker_pool = Pool(pool_size)
        self.http = WSGIServer(('', port), self.app.wsgi_app, spawn=self.worker_pool)
        self.http.start()

    # Exposed Request Endpoints

    def request_healthcheck(self):
        with self.app.app_context():
            return Response({"healthy": True})

    def request_status(self):
        with self.app.app_context():
            status = {
                "kernel" : self.kernel is not None,
                "topics" : {k : v.get_status() for k,v in self.schema_handlers.items()}
            }
            return jsonify(status)

class SchemaHandler(object):

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
            ORDER BY e.modified ASC
            LIMIT %d;
        '''

    def __init__(self, server_handler, schema):
        self.context = server_handler
        self.logger = self.context.logger
        self.name = schema.name
        self.modified = "2018-06-11T10:11:38.202313"
        self.status = {"latest_msg":None}
        self.pg_creds = self.context.settings.get('postgres_connection_info')
        try:
            self.topic_name = self.context.settings \
                .get('topic_settings', {}) \
                .get('name_modifier', "%s") \
                % self.name
        except Exception as err:
            print(err)
            self.topic_name = self.name
        self.update_schema(schema)
        self.set_offset("a")
        print(self.get_offset())


    def updates_available(self):
        query = SchemaHandler.NEW_STR % (self.modified, self.name)
        with psycopg2.connect(**self.pg_creds) as conn:
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(query);
            return sum([1 for i in cursor]) > 0

    def update_schema(self, schema_def):
        pass

    def get_status(self):
        return self.status

    def get_offset(self):
        try:
            offset = Offset.get_offset(self.name)
            if offset:
                return offset.offset_value
            else:
                raise ValueError('No entry for %s' % self.name)
        except Exception as err:
            msg = 'Could not get offset for %s | %s' % (self.name, err)
            self.logger.error(msg)
            self.status['latest_msg'] = msg
            return ""

    def set_offset(self, offset):
        ok = Offset.update(self.name, offset)
        if not ok:
            self.logger.info('Creating new offset entry for %s' % self.name)
            Offset.create(schema_name=self.name, offset_value=offset)
        self.status['offset'] = offset


def main():
    settings = Settings(test=False)
    handler = ServerHandler(settings)
