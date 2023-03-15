# Copyright (C) 2023 by eHealth Africa : http://www.eHealthAfrica.org
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
import signal
import socket

from confluent_kafka.admin import AdminClient

import gevent

from aether.producer.db import init as init_offset_db
from aether.producer.settings import (
    KAFKA_SETTINGS,
    REVISION,
    SETTINGS,
    VERSION,
)
from aether.producer.topic import RealmManager
from aether.producer.server import ServerMixin

# How to access Kernel: API (default) | DB
if SETTINGS.get('kernel_access_type', 'api').lower() != 'db':
    from aether.producer.kernel_api import KernelAPIClient as KernelClient
else:
    from aether.producer.kernel_db import KernelDBClient as KernelClient


class ProducerManager(ServerMixin):
    # ServerMixin Serves status & healthcheck over HTTP
    # Dispatches Signals
    # Keeps track of schemas
    # Spawns a RealmManager for each schema type in Kernel
    # RealmManager registers own eventloop greenlet (update_kafka) with ProducerManager

    killed = False

    kernel_client = None
    kafka_admin_client = None

    kafka_last_submission_error = None
    realm_managers = {}
    thread_idle = {}

    def __init__(self):
        super().__init__()

        # Turn on Flask
        self.serve()

        self.logger.info(f'== Version      :  {VERSION}')
        self.logger.info(f'== Revision     :  {REVISION}')
        self.logger.info(f'== Client mode  :  {KernelClient.mode()}')

        # Start Signal Handlers
        self.killed = False
        signal.signal(signal.SIGTERM, self.kill)
        signal.signal(signal.SIGINT, self.kill)
        gevent.signal_handler(signal.SIGTERM, self.kill)

        # Initialize Offset db, Kernel and Kafka clients
        self.init_db()
        self.kernel_client = KernelClient()
        self.kafka_admin_client = AdminClient(KAFKA_SETTINGS)

        # Clear objects and start
        self.kafka_last_submission_error = None
        self.realm_managers = {}
        self.thread_idle = {}
        self.run()

        self.logger.info('Started producer service')

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

    def keep_alive_loop(self):
        # Keeps the server up in case all other threads join at the same time.
        while not self.killed:
            gevent.sleep(1)

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

    def init_db(self):
        # Connect to offset
        init_offset_db()
        self.logger.info('OffsetDB initialized')

    def get_manager(self, realm):
        return self.realm_managers.get(realm)

    # see if kafka is available
    def kafka_available(self):
        kafka_ip, kafka_port = SETTINGS.get_required('kafka_url').split(':')
        kafka_port = int(kafka_port)

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((kafka_ip, kafka_port))
            return True

        except (InterruptedError, ConnectionRefusedError, socket.gaierror) as rce:
            self.logger.critical(f'Could not connect to Kafka on url: {kafka_ip}:{kafka_port}')
            self.logger.critical(f'Connection problem: {rce}')
            return False

    def check_kernel(self):
        return self.kernel_client.check_kernel()

    def check_status(self):
        return {
            'kernel_mode': self.kernel_client.mode(),
            'kernel_last_check': self.kernel_client.last_check,
            'kernel_last_check_error': self.kernel_client.last_check_error,
            'kafka_container_accessible': self.kafka_available(),
            'kafka_broker_information': self.broker_info(),
            'kafka_last_submission_error': self.kafka_last_submission_error,
            'topics': {k: v.get_status() for k, v in self.realm_managers.items()},
        }

    def check_topics(self):
        status = {}
        for topic, manager in self.realm_managers.items():
            status[topic] = {}
            for name, sw in manager.schemas.items():
                status[topic][name] = manager.get_topic_size(sw)
        return status

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
                    self.safe_sleep(5)
                else:
                    self.safe_sleep(30)

            except Exception as err:
                self.logger.critical(f'No Kernel connection: {err}')
                self.safe_sleep(1)
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

    def thread_checkin(self, _id):
        self.thread_idle[_id] = datetime.now()

    def thread_set_inactive(self, _id):
        self.thread_idle.pop(_id, None)

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


def main():
    ProducerManager()
