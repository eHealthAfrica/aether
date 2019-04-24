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
monkey.patch_all()  # noqa
import psycogreen.gevent
psycogreen.gevent.patch_psycopg()  # noqa

from datetime import datetime
import logging
import os
import signal

import gevent
from gevent.event import AsyncResult
from gevent.queue import PriorityQueue, Queue
import json

import psycopg2
import spavro

from producer.settings import PRODUCER_CONFIG
from producer.resource import RESOURCE_HELPER, ResourceHelper

from typing import (
    ClassVar,
    Dict,
    NamedTuple,
    Union,
    TYPE_CHECKING
)

if TYPE_CHECKING:  # pragma: no cover
    from producer.resource import Resource


FILE_PATH = os.path.dirname(os.path.realpath(__file__))

logger = logging.getLogger('producer-db')
logger.propagate = False
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    '%(asctime)s [ProducerDB] %(levelname)-8s %(message)s'))
logger.addHandler(handler)
log_level = logging.getLevelName(PRODUCER_CONFIG.get('log_level', 'DEBUG'))
logger.setLevel(log_level)


class Entity(NamedTuple):
    id: str
    offset: str
    tenant: str
    decorator_id: str
    payload: Dict


class Schema(NamedTuple):
    id: str
    tenant: str
    schema: Dict[str, str]

    def as_avro_schema(self):
        return spavro.schema.parse(
            json.dumps(self.schema)
        )


class Decorator(NamedTuple):
    id: str
    tenant: str
    serialize_mode: str
    topic_name: str
    schema_id: str


class Offset(NamedTuple):
    type: str
    value: str
    modified: str


class OffsetManager(object):
    resource_helper: ResourceHelper
    _type: ClassVar[str] = 'offset'
    _value_field: ClassVar[str] = 'value'
    _updated_field: ClassVar[str] = 'modified'

    def __init__(self, resource_helper: ResourceHelper):
        self.resource_helper = resource_helper

    def get(self, offset_type: str) -> Offset:
        # raises ValueError
        res: Resource = self.resource_helper.get(
            offset_type, OffsetManager._type
        )
        return Offset(
            offset_type,
            res.data[OffsetManager._value_field],
            res.data[OffsetManager._updated_field]
        )

    def set(self, offset_type: str, value: str) -> None:
        resource = {
            'id': offset_type,
            OffsetManager._value_field: value,
            OffsetManager._updated_field: datetime.now().isoformat()
        }
        self.resource_helper.add(offset_type, resource, OffsetManager._type)


class PriorityDatabasePool(object):

    # The large number of requests AEP makes was having a bad time with SQLAlchemy's
    # QueuePool implementation, causing a large number of connections in the pool to
    # be occupied, eventually overflowing. Additionally, a normal FIFO queue was
    # causing imporant operations like offset.set() to sit idle for longer than acceptable.
    # The priority queue is implemented to respect both stated priority and insert order.
    # So effectively for each priority level, a FIFO queue is implemented.

    def __init__(self, pg_creds, name, max_connections=1):
        self.name = name
        self.live_workers = 0
        self.pg_creds = pg_creds
        logger.debug(pg_creds)
        self.max_connections = max_connections
        logger.debug(f'Initializing DB Pool: {self.name} with {max_connections} connections.')
        self.workers = []
        self.backlog = 0
        self.max_backlog = 0
        self.job_queue = PriorityQueue()
        self.connection_pool = Queue()
        self.running = True
        gevent.signal(signal.SIGTERM, self._kill)
        self._start_workers()

    def _start_workers(self):
        for i in range(self.max_connections):
            self.connection_pool.put(self._make_connection())
        for i in range(self.max_connections):
            self.workers.append(gevent.spawn(self._dispatcher))

    def _test_connection(self, conn):
        # To take dead connections out of the pool, we run a cheap operation
        # when they're pulled from the pool.
        if not conn:
            return False
        try:
            cur = conn.cursor()
            cur.execute('SELECT 1')
            return True
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            return False

    def _make_connection(self):
        # Connection factory
        conn = psycopg2.connect(**self.pg_creds)
        logger.debug(f'Creating connection with ID {self.live_workers}')
        self.live_workers += 1
        return conn

    def _kill(self, *args, **kwargs):
        logger.info(f'PriorityDatabasePool: {self.name} is shutting down.')
        logger.info(f'PriorityDatabasePool: {self.name}'
                    f' resolving remaning {len(self.job_queue)} jobs.')
        self.running = False

    def _dispatcher(self):
        # Dispatch function, with 1 dispatcher running per allocated connection.
        while self.running or not self.job_queue.empty():
            if not self.connection_pool.empty() and not self.job_queue.empty():
                conn = self.connection_pool.get()
                priority_level, request_time, data = self.job_queue.get()
                name, promise = data
                logger.debug(f'{self.name} pulled 1 for {name}: still {len(self.connection_pool)}')
                sleep(0)  # allow other coroutines to work
                while not self._test_connection(conn):
                    logger.error(f'Pooled connection is dead, getting new resource')
                    logger.error(f'Replacing dead pool member.')
                    conn = self._make_connection()
                    sleep(0)
                logger.debug(f'Got job from {name} @priority {priority_level}')
                promise.set(conn)
                sleep(0)
            elif not self.job_queue.empty():
                self.backlog = len(self.job_queue)
                if self.backlog:
                    logger.debug(f'{self.name} has job backlog of {self.backlog}')
                sleep(0.1)
            else:
                sleep(0.1)
        self._shutdown_pool()

    def request_connection(self, priority_level, name):
        # Level 0 is the highest priority.
        promise = AsyncResult()
        job = (priority_level, datetime.now(), (name, promise))
        self.job_queue.put(job)
        return promise

    def release(self, caller, conn):
        if not conn:
            raise TypeError('Null connection returned to pool')
        self.connection_pool.put(conn)
        logger.debug(f'{caller} released. {len(self.connection_pool)} available in {self.name}')

    def _shutdown_pool(self):
        c = 1
        while not self.connection_pool.empty():
            try:
                conn = self.connection_pool.get()
                conn.close()
                logger.debug(f'{self.name} shutdown connection #{c}')
            except Exception as err:
                logger.error(f'{self.name} FAILED to shutdown connection #{c} | err: {err}')
            finally:
                c += 1


# Offset
OFFSET_MANAGER = OffsetManager(RESOURCE_HELPER)

# KernelDB
pg_requires = ['user', 'dbname', 'port', 'host', 'password']
pg_creds = {key: PRODUCER_CONFIG.get(
    "postgres_%s" % key) for key in pg_requires}
kernel_db_pool_size = PRODUCER_CONFIG.get('kernel_db_pool_size', 6)
KERNEL_DB = PriorityDatabasePool(pg_creds, 'KernelDB', kernel_db_pool_size)  # imported from here
