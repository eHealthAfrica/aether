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

from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

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

    offset_db_host = SETTINGS['offset_db_host']
    offset_db_user = SETTINGS['offset_db_user']
    offset_db_port = SETTINGS['offset_db_port']
    offset_db_password = SETTINGS['offset_db_password']
    offset_db_name = SETTINGS['offset_db_name']

    url = f'postgresql+psycopg2://{offset_db_user}:{offset_db_password}' + \
        f'@{offset_db_host}:{offset_db_port}/{offset_db_name}'

    engine = create_engine(url)
    try:
        start_session(engine)
        return
    except SQLAlchemyError:
        pass
    try:
        logger.error('Attempting to Create Database.')
        create_db(engine, url)
        start_session(engine)
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

    schema_name = Column(String, primary_key=True)
    offset_value = Column(String, nullable=False)

    @classmethod
    def create(cls, **kwargs):
        offset = Offset.get(**kwargs)
        if offset:
            return offset
        offset = cls(**kwargs)
        session = get_session()
        session.add(offset)
        session.commit()
        return offset

    @classmethod
    def get(cls, **kwargs):
        session = get_session()
        offset = session.query(cls).filter_by(**kwargs).first()
        return offset

    @classmethod
    def update(cls, name, offset_value):
        # Update or Create if not existing
        try:
            session = get_session()
            offset = session.query(cls).filter_by(
                schema_name=name
            ).first()
            if offset:
                offset.offset_value = offset_value
                session.add(offset)
                session.commit()
                return offset
            else:
                offset = cls(
                    schema_name=name,
                    offset_value=offset_value
                )
                session.add(offset)
                session.commit()
                return offset
        except Exception as err:
            logger.error('Could not save offset for topic %s | %s' %
                         (name, err))
            return offset

    @classmethod
    def get_offset(cls, name):
        session = get_session()
        offset = session.query(cls).filter_by(
            schema_name=name
        ).first()
        return offset


class PriorityDatabasePool(object):

    def __init__(self, max_connections=1):
        self.live_workers = 0
        pg_requires = ['user', 'dbname', 'port', 'host', 'password']
        self.pg_creds = {key: SETTINGS.get(
            "postgres_%s" % key) for key in pg_requires}
        self.max_connections = max_connections
        logger.debug(f'Initializing DB Pool with {max_connections} connections.')
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
        # gevent.joinall(self.workers)

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
        logger.info('PriorityDatabasePool is shutting down.')
        logger.info('PriorityDatabasePool resolving remaning %s jobs.' % (len(self.job_queue)))
        self.running = False

    def _dispatcher(self):
        while self.running or not self.job_queue.empty():
            if not self.connection_pool.empty() and not self.job_queue.empty():
                conn = self.connection_pool.get()
                while not self._test_connection(conn):
                    logger.error(f'Pooled connection is dead, getting new resource')
                    sleep(3)
                    new_id = self.live_workers
                    conn = psycopg2.connect(**self.pg_creds)
                    logger.error(f'Replaced dead pool member with {new_id}')
                    self.live_workers += 1
                priority_level, request_time, data = self.job_queue.get()
                name, promise = data
                logger.debug(f'Got job from {name} @priority {priority_level}')
                promise.set(conn)
            else:
                sleep(0)

    def request_connection(self, priority_level, name):
        promise = AsyncResult()
        job = (priority_level, datetime.now(), (name, promise))
        self.job_queue.put(job)
        return promise

    def release(self, caller, conn):
        logger.debug(f'{caller} released connection.')
        self.connection_pool.put(conn)
