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

from datetime import datetime
from functools import wraps
import json
import signal
import socket

from confluent_kafka.admin import AdminClient
from flask import Flask, request, Response

import gevent
from gevent.pool import Pool
from gevent.pywsgi import WSGIServer

from aether.producer.db import init as init_offset_db
from aether.producer.settings import (
    KAFKA_SETTINGS,
    LOG_LEVEL,
    REVISION,
    SETTINGS,
    VERSION,
    get_logger,
)
from aether.producer.topic import KafkaStatus, TopicStatus, RealmManager


# How to access Kernel: API (default) | DB
if SETTINGS.get('kernel_access_type', 'api').lower() != 'db':
    from aether.producer.kernel_api import KernelAPIClient as KernelClient
else:
    from aether.producer.kernel_db import KernelDBClient as KernelClient


class ProducerManager(object):
    # Serves status & healthcheck over HTTP
    # Dispatches Signals
    # Keeps track of schemas
    # Spawns a RealmManager for each schema type in Kernel
    # RealmManager registers own eventloop greenlet (update_kafka) with ProducerManager

    killed = False

    admin_name = None
    admin_password = None

    kernel_client = None
    kafka_admin_client = None

    kafka_status = KafkaStatus.SUBMISSION_PENDING
    realm_managers = {}
    thread_idle = {}

    def __init__(self):
        # Start Signal Handlers
        self.killed = False
        signal.signal(signal.SIGTERM, self.kill)
        signal.signal(signal.SIGINT, self.kill)
        gevent.signal_handler(signal.SIGTERM, self.kill)

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
        self.realm_managers = {}
        self.thread_idle = {}
        self.run()

        self.logger.info('Started producer service')
        self.logger.info(f'== Version      :  {VERSION}')
        self.logger.info(f'== Revision     :  {REVISION}')
        self.logger.info(f'== Client mode  :  {self.kernel_client.mode()}')
        self.logger.info(f'== Kafka status :  {self.kafka_status}')

    def keep_alive_loop(self):
        # Keeps the server up in case all other threads join at the same time.
        while not self.killed:
            gevent.sleep(1)

    def run(self):
        self.threads = []
        self.threads.append(gevent.spawn(self.keep_alive_loop))
        self.threads.append(gevent.spawn(self.check_realms))
        # Also going into this greenlet pool:
        # Each RealmManager.update_kafka() from RealmManager.init
        gevent.joinall(self.threads)

    def kill(self, *args, **kwargs):
        # Stops HTTP service and flips stop switch, which is read by greenlets
        self.logger.warn('Shutting down gracefully')
        self.http.stop()
        self.http.close()
        self.worker_pool.kill()
        self.killed = True  # Flag checked by spawned RealmManagers to stop themselves

    def safe_sleep(self, dur):
        # keeps shutdown time low by yielding during sleep and checking if killed.
        # limit sleep calls to prevent excess context switching that occurs on gevent.sleep
        if dur < 5:
            unit = 1
        else:
            res = dur % 5
            dur = (dur - res) / 5
            unit = 5
            gevent.sleep(res)
        for _x in range(int(dur)):
            if not self.killed:
                gevent.sleep(unit)

    # Connectivity

    # see if kafka's port is available
    def kafka_available(self):
        kafka_ip, kafka_port = SETTINGS.get_required('kafka_url').split(':')
        kafka_port = int(kafka_port)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((kafka_ip, kafka_port))
        except (InterruptedError, ConnectionRefusedError, socket.gaierror) as rce:
            self.logger.error(f'Could not connect to Kafka on url: {kafka_ip}:{kafka_port}')
            self.logger.error(f'Connection problem: {rce}')
            return False
        return True

    def broker_info(self):
        try:
            res = {'brokers': [], 'topics': []}
            md = self.kafka_admin_client.list_topics(timeout=10)
            for b in iter(md.brokers.values()):
                if b.id == md.controller_id:
                    res['brokers'].append(f'{b}  (controller)')
                else:
                    res['brokers'].append(f'{b}')

            for t in iter(md.topics.values()):
                topics = []

                msg_t = ', '.join([
                    f'{str(t)} with {len(t.partitions)} partition(s)',
                    (f'error: {t.error}' if t.error is not None else ''),
                ])
                topics.append(msg_t)

                for p in iter(t.partitions.values()):
                    msg_p = ', '.join([
                        f'partition: {p.id}',
                        f'leader: {p.leader}',
                        f'replicas: {p.replicas}',
                        f'isrs: {p.isrs}',
                        (f'error: {p.error}' if p.error is not None else ''),
                    ])
                    topics.append(msg_p)

                res['topics'].append(topics)
            return res
        except Exception as err:
            return {'error': f'{err}'}

    def thread_checkin(self, _id):
        self.thread_idle[_id] = datetime.now()

    def thread_set_inactive(self, _id):
        if _id in self.thread_idle:
            del self.thread_idle[_id]

    # Connect to offset
    def init_db(self):
        init_offset_db()
        self.logger.info('OffsetDB initialized')

    # TODO swap over

    # # main update loop
    # # creates a manager / producer for each Realm
    def check_realms(self):
        while not self.killed:
            realms = []
            try:
                self.logger.debug('Checking for new realms')
                realms = self.kernel_client.get_realms()
                for realm in realms:
                    if realm not in self.realm_managers.keys():
                        self.logger.info(f'Realm connected: {realm}')
                        self.realm_managers[realm] = RealmManager(self, realm)
                if not realms:
                    gevent.sleep(5)
                else:
                    gevent.sleep(30)
            except Exception as err:
                self.logger.critical(f'No Kernel connection: {err}')
                gevent.sleep(1)
                continue
        self.logger.debug('No longer checking for new Realms')

    def check_thread_health(self):
        max_idle = SETTINGS.get('MAX_JOB_IDLE_SEC', 600)
        idle_times = self.get_thread_idle()
        if not idle_times:
            return {}
        self.logger.debug(f'idle times (s) {idle_times}')
        expired = {k: v for k, v in idle_times.items() if v > max_idle}
        if expired:
            self.logger.error(f'Expired threads (s) {expired}')
        return expired

    def get_thread_idle(self):
        _now = datetime.now()
        # if a job is inactive (stopped / paused intentionally or died naturally)
        # or if a job is still starting up
        # then it's removed from the check and given a default value of _now
        idle_times = {_id: int((_now - self.thread_idle.get(_id, _now)).total_seconds())
                      for _id in self.realm_managers.keys()}
        return idle_times

    # Flask Functions

    def add_endpoints(self):
        # public
        self.register('health', self.request_health)
        self.register('healthcheck', self.request_healthcheck)
        self.register('kernelcheck', self.request_kernelcheck)
        self.register('kafkacheck', self.request_kafkacheck)
        self.register('check-app', self.request_check_app)
        self.register('check-app/aether-kernel', self.request_kernelcheck)
        self.register('check-app/kafka', self.request_kafkacheck)
        # protected
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
        with self.app.app_context():
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

    def request_health(self):
        with self.app.app_context():
            return Response({'healthy': True}, content_type='application/json')

    def request_healthcheck(self):
        with self.app.app_context():
            try:
                expired = self.check_thread_health()
                if not expired:
                    return Response({'healthy': True}, content_type='application/json')
                else:
                    return Response(
                        json.dumps(expired),
                        500,
                        content_type='application/json'
                    )
            except Exception as err:
                self.app.logger.error(f'Unexpected HC error: {err}')
                return Response(f'Unexpected error: {err}', 500)

    def request_kernelcheck(self):
        with self.app.app_context():
            healthy = self.kernel_client.check_kernel()
            return Response(
                {'healthy': healthy},
                status=200 if healthy else 424,  # Failed dependency
                content_type='application/json',
            )

    def request_kafkacheck(self):
        with self.app.app_context():
            healthy = self.kafka_available()
            return Response(
                {'healthy': healthy},
                status=200 if healthy else 424,  # Failed dependency
                content_type='application/json',
            )

    def request_check_app(self):
        with self.app.app_context():
            return Response(
                {
                    'app_name': 'aether-producer',
                    'app_version': VERSION,
                    'app_revision': REVISION,
                },
                content_type='application/json',
            )

    @requires_auth
    def request_status(self):
        with self.app.app_context():
            status = {
                'kernel_mode': self.kernel_client.mode(),
                'kernel_last_check': self.kernel_client.last_check,
                'kernel_last_check_error': self.kernel_client.last_check_error,
                'kafka_container_accessible': self.kafka_available(),
                'kafka_broker_information': self.broker_info(),
                'kafka_submission_status': str(self.kafka_status),  # This is just a status flag
                'topics': {k: v.get_status() for k, v in self.realm_managers.items()},
            }
            return Response(status, content_type='application/json')

    @requires_auth
    def request_topics(self):
        with self.app.app_context():
            status = {}
            for topic, manager in self.realm_managers.items():
                status[topic] = {}
                for name, sw in manager.schemas.items():
                    status[topic][name] = manager.get_topic_size(sw)

            return Response(status, content_type='application/json')

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
        with self.app.app_context():
            topic = request.args.get('topic')
            realm = request.args.get('realm')
            if not realm:
                return Response('A realm must be specified', 422)
            if not topic:
                return Response('A topic must be specified', 422)
            if not self.realm_managers.get(realm):
                return Response(f'Bad realm name: {realm}', 422)

            manager = self.realm_managers[realm]
            schema_wrapper = manager.schemas.get(topic)
            if not schema_wrapper:
                return Response(f'realm {realm} has no topic {topic}', 422)
            if status is TopicStatus.PAUSED:
                fn = manager.pause
            if status is TopicStatus.NORMAL:
                fn = manager.resume
            if status is TopicStatus.REBUILDING:
                fn = manager.rebuild

            try:
                res = fn(schema_wrapper)
                if not res:
                    return Response(f'Operation failed on {topic}', 500)

                return Response(f'Success for status {status} on {topic}', 200)
            except Exception as err:
                return Response(f'Operation failed on {topic} with: {err}', 500)


def main():
    ProducerManager()
