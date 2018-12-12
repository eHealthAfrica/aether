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
from gevent import sleep
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
    __tablename__ = 'offset'

    GET_STR = '''
        SELECT
            o.schema_name,
            o.offset_value
        FROM public.offset o
        WHERE o.schema_name = {schema_name}
        LIMIT 1; '''

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
        # OffsetDB
        offset_settings = {
            'user': 'offset_db_user',
            'dbname': 'offset_db_name',
            'port': 'offset_db_port',
            'host': 'offset_db_host',
            'password': 'offset_db_password'
        }
        offset_creds = {k: SETTINGS.get(v) for k, v in offset_settings.items()}
        global OFFSET_DB
        OFFSET_DB = PriorityDatabasePool(offset_creds, 'OffsetDB', 3)

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
            OFFSET_DB.release(call, conn)

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
            OFFSET_DB.release(call, conn)
    

class PriorityDatabasePool(object):

    def __init__(self, pg_creds, name, max_connections=1):
        self.name = name
        self.live_workers = 0
        self.pg_creds = pg_creds
        self.max_connections = max_connections
        logger.debug(f'Initializing DB Pool: {self.name} with {max_connections} connections.')
        self.workers = []
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
        if not conn:
            return False
        try:
            cur = conn.cursor()
            cur.execute('SELECT 1')
            return True
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            return False

    def _make_connection(self):
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
        while self.running or not self.job_queue.empty():
            if not self.connection_pool.empty() and not self.job_queue.empty():
                conn = self.connection_pool.get()
                priority_level, request_time, data = self.job_queue.get()
                name, promise = data
                logger.debug(f'{self.name} pulled 1 for {name}: still {len(self.connection_pool)}')
                while not self._test_connection(conn):
                    logger.error(f'Pooled connection is dead, getting new resource')
                    logger.error(f'Replacing dead pool member.')
                    conn = self._make_connection()
                    sleep(0)
                logger.debug(f'Got job from {name} @priority {priority_level}')
                promise.set(conn)
                sleep(0)
            else:
                sleep(0)

    def request_connection(self, priority_level, name):
        promise = AsyncResult()
        job = (priority_level, datetime.now(), (name, promise))
        self.job_queue.put(job)
        return promise

    def release(self, caller, conn):
        if not conn:
            raise TypeError('Null connection returned to pool')
        self.connection_pool.put(conn)
        logger.debug(f'{caller} released. {len(self.connection_pool)} available in {self.name}')

# KernelDB
pg_requires = ['user', 'dbname', 'port', 'host', 'password']
pg_creds = {key: SETTINGS.get(
    "postgres_%s" % key) for key in pg_requires}
KERNEL_DB = PriorityDatabasePool(pg_creds, 'KernelDB', 20)
