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
import sys
import os
import signal
import uuid

import gevent
from gevent.event import AsyncResult
from gevent.queue import PriorityQueue, Queue

import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor

from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from producer.settings import Settings

FILE_PATH = os.path.dirname(os.path.realpath(__file__))

Base = declarative_base()
logger = logging.getLogger('producer-db')
logger.propagate = False
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    '%(asctime)s [ProducerDB] %(levelname)-8s %(message)s'))
logger.addHandler(handler)
engine = None
Session = None

file_path = os.environ.get('PRODUCER_SETTINGS_FILE')
SETTINGS = Settings(file_path)
log_level = logging.getLevelName(SETTINGS.get('log_level', 'DEBUG'))
logger.setLevel(log_level)


def init():
    global engine

    # Offset

    offset_db_host = SETTINGS['offset_db_host']
    offset_db_user = SETTINGS['offset_db_user']
    offset_db_port = SETTINGS['offset_db_port']
    offset_db_password = SETTINGS['offset_db_password']
    offset_db_name = SETTINGS['offset_db_name']

    url = f'postgresql+psycopg2://{offset_db_user}:{offset_db_password}' + \
        f'@{offset_db_host}:{offset_db_port}/{offset_db_name}'

    engine = create_engine(url, poolclass=NullPool)
    try:
        start_session(engine)
        Offset.create_pool()
        return
    except SQLAlchemyError:
        pass
    try:
        logger.error('Attempting to Create Database.')
        create_db(engine, url)
        start_session(engine)
        Offset.create_pool()
    except SQLAlchemyError as sqe:
        logger.error('Database creation failed: %s' % sqe)
        sys.exit(1)


def start_session(engine):
    try:
        Base.metadata.create_all(engine)

        global Session
        Session = sessionmaker(bind=engine)

        logger.info('Database initialized.')
    except SQLAlchemyError as err:
        logger.error('Database could not be initialized. | %s' % err)
        raise err


def create_db(engine, url):
    db_name = url.split('/')[-1]
    root = url.replace(db_name, 'postgres')
    temp_engine = create_engine(root)
    conn = temp_engine.connect()
    conn.execute("commit")
    conn.execute("create database %s" % db_name)
    conn.close()


def get_session():
    return Session()


def get_engine():
    return engine


def make_uuid():
    return str(uuid.uuid4())


class Offset(Base):

    # SQLAlchemy is now only used for table creation.
    # All gets and sets to offset are made via psycopg2 which
    # allows us to use the priority connection pooling, making
    # sure our sets happen ASAP while reads of offsets can be
    # delayed until resources are free.

    __tablename__ = 'offset_table'

    # GET single offset value
    GET_STR = '''
        SELECT
            o.schema_name,
            o.offset_value
        FROM public.offset o
        WHERE o.schema_name = {schema_name}
        LIMIT 1; '''

    # UPSERT Postgres call.
    SET_STR = '''
        INSERT INTO public.offset
            (schema_name, offset_value)
        VALUES
            ({schema_name}, {offset_value})
        ON CONFLICT (schema_name) DO UPDATE SET
            (schema_name, offset_value)
            = (EXCLUDED.schema_name, EXCLUDED.offset_value);'''

    schema_name = Column(String, primary_key=True)
    offset_value = Column(String, nullable=False)

    @classmethod
    def create_pool(cls):
        # Creates connection pool to OffsetDB as part of initialization.
        offset_settings = {
            'user': 'offset_db_user',
            'dbname': 'offset_db_name',
            'port': 'offset_db_port',
            'host': 'offset_db_host',
            'password': 'offset_db_password'
        }
        offset_creds = {k: SETTINGS.get(v) for k, v in offset_settings.items()}
        global OFFSET_DB
        offset_db_pool_size = SETTINGS.get('offset_db_pool_size', 6)
        OFFSET_DB = PriorityDatabasePool(offset_creds, 'OffsetDB', offset_db_pool_size)

    @classmethod
    def update(cls, name, offset_value):
        # Update or Create if not existing
        call = "Offset-SET"
        try:
            promise = OFFSET_DB.request_connection(0, call)  # Highest Priority
            conn = promise.get()
            cursor = conn.cursor()
            query = sql.SQL(Offset.SET_STR).format(
                schema_name=sql.Literal(name),
                offset_value=sql.Literal(offset_value))
            cursor.execute(query)
            conn.commit()
            return offset_value
        except Exception as err:
            raise err
        finally:
            try:
                OFFSET_DB.release(call, conn)
            except UnboundLocalError:
                logger.error(f'{call} could not release a connection it never received.')

    @classmethod
    def get_offset(cls, name):
        call = "Offset-GET"
        try:
            promise = OFFSET_DB.request_connection(1, call)  # Lower Priority than set
            conn = promise.get()
            cursor = conn.cursor(cursor_factory=DictCursor)
            query = sql.SQL(Offset.GET_STR).format(schema_name=sql.Literal(name))
            cursor.execute(query)
            res = [i for i in cursor]
            if not res:
                return None
            return res[0][1]
        except Exception as err:
            raise err
        finally:
            try:
                OFFSET_DB.release(call, conn)
            except UnboundLocalError:
                logger.error(f'{call} could not release a connection it never received.')


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
        logger.info(f'PriorityDatabasePool: {self.name}' +
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


# KernelDB
pg_requires = ['user', 'dbname', 'port', 'host', 'password']
pg_creds = {key: SETTINGS.get(
    "postgres_%s" % key) for key in pg_requires}
kernel_db_pool_size = SETTINGS.get('kernel_db_pool_size', 6)
KERNEL_DB = PriorityDatabasePool(pg_creds, 'KernelDB', kernel_db_pool_size)  # imported from here
