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

# flake8: noqa: E402

# need to patch sockets to make requests async
from gevent import monkey
monkey.patch_all()
import psycogreen.gevent
psycogreen.gevent.patch_psycopg()

from datetime import datetime
import signal
import sys

import gevent
from gevent import monkey, sleep
from gevent.event import AsyncResult
from gevent.queue import PriorityQueue, Queue

import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor

from sqlalchemy import Column, String, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from aether.producer.settings import SETTINGS, get_logger

Base = declarative_base()
logger = get_logger('producer-db')


class PriorityDatabasePool(object):

    # The large number of requests AEP makes was having a bad time with SQLAlchemy's
    # QueuePool implementation, causing a large number of connections in the pool to
    # be occupied, eventually overflowing. Additionally, a normal FIFO queue was
    # causing important operations like offset.set() to sit idle for longer than acceptable.
    # The priority queue is implemented to respect both stated priority and insert order.
    # So effectively for each priority level, a FIFO queue is implemented.

    def __init__(self, pg_creds, name, max_connections=1):
        self.name = name
        self.live_workers = 0
        self.pg_creds = pg_creds
        self.max_connections = int(max_connections)
        logger.debug(f'Initializing DB Pool: {self.name} with {max_connections} connections.')

        self.workers = []
        self.backlog = 0
        self.max_backlog = 0
        self.job_queue = PriorityQueue()
        self.connection_pool = Queue()
        self.running = True
        # Start Signal Handlers
        self.killed = False
        signal.signal(signal.SIGTERM, self._kill)
        signal.signal(signal.SIGINT, self._kill)
        gevent.signal_handler(signal.SIGTERM, self._kill)

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
                    logger.warning('Pooled connection is dead, getting new resource.'
                                   ' Replacing dead pool member.')
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
                logger.warning(f'{self.name} FAILED to shutdown connection #{c} | err: {err}')
            finally:
                c += 1


class Offset(Base):

    # SQLAlchemy is now only used for table creation.
    # All gets and sets to offset are made via psycopg2 which
    # allows us to use the priority connection pooling, making
    # sure our sets happen ASAP while reads of offsets can be
    # delayed until resources are free.

    __tablename__ = 'offset'
    schema_name = Column(String, primary_key=True)
    offset_value = Column(String, nullable=False)

    # private connection pool
    __pool__ = None

    # GET single offset value
    GET_STR = '''
        SELECT offset_value
          FROM public.offset
         WHERE schema_name = {schema_name}
         LIMIT 1;
    '''

    # UPSERT Postgres call
    SET_STR = '''
        INSERT INTO public.offset
            (schema_name, offset_value)
        VALUES
            ({schema_name}, {offset_value})
        ON CONFLICT (schema_name)
        DO UPDATE SET
            (schema_name, offset_value) = (EXCLUDED.schema_name, EXCLUDED.offset_value);
    '''

    @classmethod
    def create_pool(cls):
        if not Offset.__pool__:
            # Creates connection pool to OffsetDB as part of initialization.
            offset_settings = {
                'user': 'offset_db_user',
                'dbname': 'offset_db_name',
                'port': 'offset_db_port',
                'host': 'offset_db_host',
                'password': 'offset_db_password'
            }
            offset_creds = {k: SETTINGS.get_required(v) for k, v in offset_settings.items()}
            offset_db_pool_size = int(SETTINGS.get('offset_db_pool_size', 6))
            Offset.__pool__ = PriorityDatabasePool(offset_creds, 'OffsetDB', offset_db_pool_size)
        return Offset.__pool__

    @classmethod
    def close_pool(cls):
        if Offset.__pool__:
            Offset.__pool__._kill()
            Offset.__pool__ = None

    @classmethod
    def update(cls, name, offset_value):
        # Update or Create if not existing
        call = 'Offset-SET'
        try:
            promise = Offset.__pool__.request_connection(0, call)  # Highest Priority
            conn = promise.get()
            cursor = conn.cursor()
            query = sql.SQL(Offset.SET_STR).format(
                schema_name=sql.Literal(name),
                offset_value=sql.Literal(offset_value),
            )
            cursor.execute(query)
            conn.commit()
            return offset_value

        except Exception as err:
            logger.warning(err)
            raise err

        finally:
            try:
                Offset.__pool__.release(call, conn)
            except UnboundLocalError:
                logger.warning(f'{call} could not release a connection it never received.')

    @classmethod
    def get_offset(cls, name):
        call = 'Offset-GET'
        try:
            promise = Offset.__pool__.request_connection(1, call)  # Lower Priority than set
            conn = promise.get()
            cursor = conn.cursor(cursor_factory=DictCursor)
            query = sql.SQL(Offset.GET_STR).format(schema_name=sql.Literal(name))
            cursor.execute(query)
            res = [i for i in cursor]
            return res[0][0] if res else None

        except Exception as err:
            logger.warning(err)
            raise err

        finally:
            try:
                Offset.__pool__.release(call, conn)
            except UnboundLocalError:
                logger.warning(f'{call} could not release a connection it never received.')


def init():
    def _db_url(db_name):
        return (
            f'postgresql+psycopg2://{offset_db_user}:{offset_db_password}'
            f'@{offset_db_host}:{offset_db_port}/{db_name}'
        )

    def _start_session(engine):
        try:
            Base.metadata.create_all(engine)
            sessionmaker(bind=engine)
            logger.info('Database initialized.')
        except SQLAlchemyError as err:
            logger.warning(f'Database could not be initialized | {err}')
            raise err

    def _create_db():
        logger.info(f'Attempting to create database "{offset_db_name}".')
        temp_engine = create_engine(_db_url('postgres'))
        conn = temp_engine.connect()
        conn.execute('commit')
        conn.execute(f'CREATE DATABASE {offset_db_name};')
        conn.close()
        logger.info(f'Database "{offset_db_name}" created.')

    # Offset
    offset_db_host = SETTINGS.get_required('offset_db_host')
    offset_db_user = SETTINGS.get_required('offset_db_user')
    offset_db_port = SETTINGS.get_required('offset_db_port')
    offset_db_password = SETTINGS.get_required('offset_db_password')
    offset_db_name = SETTINGS.get_required('offset_db_name')

    engine = create_engine(_db_url(offset_db_name), poolclass=NullPool)
    try:
        _start_session(engine)
        Offset.create_pool()
        return
    except SQLAlchemyError as sqe:
        logger.warning(f'Start session failed (1st attempt): {sqe}')
        pass

    # it was not possible to start session because the database does not exit
    # create it and try again
    try:
        _create_db()
        _start_session(engine)
        Offset.create_pool()
    except SQLAlchemyError as sqe:
        logger.critical(f'Start session failed (2nd attempt): {sqe}')
        logger.exception(sqe)
        sys.exit(1)
