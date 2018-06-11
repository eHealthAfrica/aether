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
import gevent
from gevent.pool import Pool
import io
import json
import os
import psycopg2
import signal
import spavro.schema
import sys

from aether.client import KernelClient
from flask import Flask, Response, request, abort, jsonify
from gevent.pywsgi import WSGIServer
from confluent_kafka import Producer #  KafkaConsumer
from psycopg2.extras import DictCursor
from spavro.datafile import DataFileWriter
from spavro.io import DatumWriter
from spavro.io import validate


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


class ServerHandler(object):
    def __init__(self, settings):
        self.settings = settings
        self.serve()
        self.killed = False
        signal.signal(signal.SIGTERM, self.kill)
        signal.signal(signal.SIGINT, self.kill)
        gevent.signal(signal.SIGTERM, self.kill)
        self.schema_handlers = {}
        self.add_endpoints()
        print(settings)
        self.kernel = None
        self.run()

    def run(self):
        threads = []
        threads.append(gevent.spawn(self.connect_aether))
        threads.append(gevent.spawn(self.check_schemas))
        gevent.joinall(threads)

    def update_schemas(self):
        pass

    def kill(self, *args, **kwargs):
        self.http.stop()
        self.http.close()
        self.worker_pool.kill()
        self.killed = True
        self.app.logger.debug('Dead...')

    # Connectivity

    def connect_aether(self):
        print('connecting to Aether...')
        self.kernel = None
        while True:
            try:
                self.kernel = KernelClient(
                    url=self.settings['kernel_url'],
                    **self.settings['kernel_credentials']
                )
                break
            except Exception as e:
                print('No Aether connection...')
                sleep(self.settings['start_delay'])

    def check_schemas(self):
        while True and not self.killed:
            if not self.kernel:
                print('Waiting for Kernel')
                sleep(1)


    # Flask Functions

    def add_endpoints(self):
        # URLS configured here
        self.register('healthcheck', self.request_healthcheck)
        self.register('status', self.request_status)

    def register(self, route_name, fn):
        self.app.add_url_rule('/%s' % route_name, route_name, view_func=fn)

    def serve(self):
        self.app = Flask(__name__)  # pylint: disable=invalid-name
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
            status = {}
            return jsonify(status)

class SchemaHandler(object):

    def __init__(self, name):
        pass


def main():
    settings = Settings(test=False)
    handler = ServerHandler(settings)
