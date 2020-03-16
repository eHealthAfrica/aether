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

import signal
import socket
from functools import wraps

from confluent_kafka.admin import AdminClient
from flask import Flask, Response, request, jsonify

import gevent
from gevent.pool import Pool
from gevent.pywsgi import WSGIServer

from producer.db import init as init_offset_db
from producer.kernel import KernelClient
from producer.settings import KAFKA_SETTINGS, SETTINGS, LOG_LEVEL, get_logger
from producer.topic import KafkaStatus, TopicStatus, TopicManager


class ProducerManager(object):
    # Serves status & healthcheck over HTTP
    # Dispatches Signals
    # Keeps track of schemas
    # Spawns a TopicManager for each schema type in Kernel
    # TopicManager registers own eventloop greenlet (update_kafka) with ProducerManager

    def __init__(self):
        # Start Signal Handlers
        self.killed = False
        signal.signal(signal.SIGTERM, self.kill)
        signal.signal(signal.SIGINT, self.kill)
        gevent.signal(signal.SIGTERM, self.kill)

        # Turn on Flask Endpoints
        # Get Auth details from env
        self.admin_name = SETTINGS.get_required('producer_admin_user')
        self.admin_password = SETTINGS.get_required('producer_admin_pw')
        self.serve()
        self.add_endpoints()

        # Initialize Offset db, Kernel and Kafka clients
        self.init_db()
        self.kernel_client = KernelClient()
        self.kafka_admin_client = AdminClient(KAFKA_SETTINGS)

        # Clear objects and start
        self.kafka_status = KafkaStatus.SUBMISSION_PENDING
        self.topic_managers = {}
        self.run()

    def keep_alive_loop(self):
        # Keeps the server up in case all other threads join at the same time.
        while not self.killed:
            gevent.sleep(1)

    def run(self):
        self.threads = []
        self.threads.append(gevent.spawn(self.keep_alive_loop))
        self.threads.append(gevent.spawn(self.check_schemas))
        # Also going into this greenlet pool:
        # Each TopicManager.update_kafka() from TopicManager.init
        gevent.joinall(self.threads)

    def kill(self, *args, **kwargs):
        # Stops HTTP service and flips stop switch, which is read by greenlets
        self.logger.warn('Shutting down gracefully')
        self.http.stop()
        self.http.close()
        self.worker_pool.kill()
        self.killed = True  # Flag checked by spawned TopicManagers to stop themselves

    def safe_sleep(self, dur):
        # keeps shutdown time low by yielding during sleep and checking if killed.
        for x in range(int(dur)):
            if not self.killed:
                gevent.sleep(1)

    # Connectivity

    # see if kafka's port is available
    def kafka_available(self):
        kafka_ip, kafka_port = SETTINGS.get_required('kafka_url').split(':')
        kafka_port = int(kafka_port)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((kafka_ip, kafka_port))
        except (InterruptedError, ConnectionRefusedError, socket.gaierror) as rce:
            self.logger.debug(f'Could not connect to Kafka on url: {kafka_ip}:{kafka_port}')
            self.logger.debug(f'Connection problem: {rce}')
            return False
        return True

    def broker_info(self):
        try:
            res = {'brokers': [], 'topics': []}
            md = self.kafka_admin_client.list_topics(timeout=10)
            for b in iter(md.brokers.values()):
                if b.id == md.controller_id:
                    res['brokers'].append('{}  (controller)'.format(b))
                else:
                    res['brokers'].append('{}'.format(b))

            for t in iter(md.topics.values()):
                t_str = []
                if t.error is not None:
                    errstr = ': {}'.format(t.error)
                else:
                    errstr = ''

                t_str.append('{} with {} partition(s){}'.format(t, len(t.partitions), errstr))

                for p in iter(t.partitions.values()):
                    if p.error is not None:
                        errstr = ': {}'.format(p.error)
                    else:
                        errstr = ''

                    t_str.append('partition {} leader: {}, replicas: {}, isrs: {}'.format(
                        p.id, p.leader, p.replicas, p.isrs, errstr))
                res['topics'].append(t_str)
            return res
        except Exception as err:
            return {'error': f'{err}'}

    # Connect to offset
    def init_db(self):
        init_offset_db()
        self.logger.info('OffsetDB initialized')

    # Main Schema Loop
    # Spawns TopicManagers for new schemas, updates schemas for workers on change.
    def check_schemas(self):
        # Checks for schemas in Kernel
        # Creates TopicManagers for found schemas.
        # Updates TopicManager.schema on schema change
        while not self.killed:
            schemas = []
            try:
                schemas = self.kernel_client.get_schemas()
            except Exception as err:
                self.logger.error(f'No Kernel connection: {err}')
                gevent.sleep(1)
                continue

            for schema in schemas:
                name = schema['schema_name']
                realm = schema['realm']
                schema_name = f'{realm}.{name}'
                if schema_name not in self.topic_managers.keys():
                    self.logger.info(f'Topic connected: {schema_name}')
                    self.topic_managers[schema_name] = TopicManager(self, schema, realm)
                else:
                    topic_manager = self.topic_managers[schema_name]
                    if topic_manager.schema_changed(schema):
                        topic_manager.update_schema(schema)
                        self.logger.debug(f'Schema {schema_name} updated')
                    else:
                        self.logger.debug(f'Schema {schema_name} unchanged')

            # Time between checks for schema change
            self.safe_sleep(SETTINGS.get('sleep_time', 1))
        self.logger.debug('No longer checking schemas')

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
        self.app.add_url_rule(f'/{route_name}', route_name, view_func=fn)

    def serve(self):
        self.app = Flask('AetherProducer')  # pylint: disable=invalid-name
        self.logger = get_logger('Producer', self.app.logger)
        if LOG_LEVEL == 'DEBUG':
            self.app.debug = True

        self.app.config['JSONIFY_PRETTYPRINT_REGULAR'] = SETTINGS \
            .get('flask_settings', {}) \
            .get('pretty_json_status', False)

        server_ip = SETTINGS.get('server_ip', '')
        server_port = int(SETTINGS.get('server_port', 5005))
        pool_size = SETTINGS.get('flask_settings', {}).get('max_connections', 3)
        self.worker_pool = Pool(pool_size)
        self.http = WSGIServer((server_ip, server_port), self.app.wsgi_app, spawn=self.worker_pool)
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
            return Response({'healthy': True})

    @requires_auth
    def request_status(self):
        status = {
            'kernel_last_check': self.kernel_client.last_check,
            'kernel_last_check_error': self.kernel_client.last_check_error,
            'kafka_container_accessible': self.kafka_available(),
            'kafka_broker_information': self.broker_info(),
            'kafka_submission_status': str(self.kafka_status),  # This is just a status flag
            'topics': {k: v.get_status() for k, v in self.topic_managers.items()},
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

    @requires_auth
    def handle_topic_command(self, request, status):
        topic = request.args.get('topic')
        if not topic:
            return Response('A topic must be specified', 422)
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


def main():
    ProducerManager()
