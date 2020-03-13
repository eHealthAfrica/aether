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

from gevent import monkey
# need to patch sockets to make requests async
monkey.patch_all()  # noqa
import psycogreen.gevent
psycogreen.gevent.patch_psycopg()  # noqa

import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor

from producer.db import PriorityDatabasePool
from producer.settings import SETTINGS, get_logger

logger = get_logger('producer-kernel')


class KernelDB(object):

    _SCHEMAS_SQL = 'SELECT * FROM kernel_schema_vw'

    _CHECK_UPDATES_SQL = '''
        SELECT id
        FROM kernel_entity_vw
        WHERE modified    > {modified}
          AND schema_name = {schema_name}
          AND realm       = {realm}
        LIMIT 1;
    '''

    _COUNT_UPDATES_SQL = '''
        SELECT COUNT(id)
        FROM kernel_entity_vw
        WHERE schema_name = {schema_name}
          AND realm       = {realm};
    '''

    _GET_UPDATES_SQL = '''
        SELECT *
        FROM kernel_entity_vw
        WHERE modified    > {modified}
          AND schema_name = {schema_name}
          AND realm       = {realm}
        ORDER BY modified ASC
        LIMIT {limit};
    '''

    def __init__(self):
        pg_requires = ['user', 'dbname', 'port', 'host', 'password']
        pg_creds = {key: SETTINGS.get(f'postgres_{key}') for key in pg_requires}
        kernel_db_pool_size = SETTINGS.get('kernel_db_pool_size', 6)

        self.pool = PriorityDatabasePool(pg_creds, 'KernelDB', kernel_db_pool_size)
        self.window_size_sec = SETTINGS.get('window_size_sec', 3)
        self.limit = SETTINGS.get('postgres_pull_limit', 100)

    def get_time_window_filter(self, query_time):
        # You can't always trust that a set from kernel made up of time window
        # start < _time < end is complete if nearly equal(_time, now()).
        # Sometimes rows belonging to that set would show up a couple mS after
        # the window had closed and be dropped. Our solution was to truncate sets
        # based on the insert time and now() to provide a buffer.
        TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'

        def fn(row):
            commited = datetime.strptime(row.get('modified')[:26], TIME_FORMAT)
            lag_time = (query_time - commited).total_seconds()
            if lag_time > self.window_size_sec:
                return True

            elif lag_time < -30.0:
                # Sometimes fractional negatives show up. More than 30 seconds is an issue though.
                logger.critical(f'INVALID LAG INTERVAL: {lag_time}. Check time settings on server.')

            _id = row.get('id')
            logger.debug(f'WINDOW EXCLUDE: ID: {_id}, LAG: {lag_time}')
            return False
        return fn

    def _exec_sql(self, name, priority, query):
        try:
            promise = self.pool.request_connection(priority, name)
            conn = promise.get()
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(query)
            return cursor

        except psycopg2.OperationalError as pgerr:
            logger.critical(f'Error while accessing database: {pgerr}')
            return None

        finally:
            try:
                self.pool.release(name, conn)
            except UnboundLocalError:
                logger.error(f'{name} could not release a connection it never received.')

    def get_schemas(self):
        name = 'schemas_query'
        query = sql.SQL(KernelDB._SCHEMAS_SQL)
        cursor = self._exec_sql(name, 1, query)
        if cursor:
            for row in cursor:
                yield {key: row[key] for key in row.keys()}
        else:
            logger.critical('Could not access db to get topics')
            return []

    def check_updates(self, modified, schema_name, realm):
        query = sql.SQL(KernelDB._CHECK_UPDATES_SQL).format(
            modified=sql.Literal(modified),
            schema_name=sql.Literal(schema_name),
            realm=sql.Literal(realm),
        )
        cursor = self._exec_sql(schema_name, 1, query)
        if cursor:
            return sum([1 for i in cursor]) > 0
        else:
            logger.critical('Could not access database to look for updates')
            return False

    def count_updates(self, schema_name, realm):
        query = sql.SQL(KernelDB._COUNT_UPDATES_SQL).format(
            schema_name=sql.Literal(schema_name),
            realm=sql.Literal(realm),
        )
        cursor = self._exec_sql(schema_name, 0, query)
        if cursor:
            size = [{key: row[key] for key in row.keys()} for row in cursor][0]
            logger.debug(f'Reporting requested size for {schema_name} of {size["count"]}')
            return size
        else:
            logger.critical('Could not access database to look for updates')
            return -1

    def get_updates(self, modified, schema_name, realm):
        query = sql.SQL(KernelDB._GET_UPDATES_SQL).format(
            modified=sql.Literal(modified),
            schema_name=sql.Literal(schema_name),
            realm=sql.Literal(realm),
            limit=sql.Literal(self.limit),
        )

        query_time = datetime.now()
        cursor = self._exec_sql(schema_name, 2, query)
        if cursor:
            window_filter = self.get_time_window_filter(query_time)
            return [
                {key: row[key] for key in row.keys()}
                for row in cursor
                if window_filter(row)
            ]
        else:
            logger.critical('Could not access database to look for updates')
            return []
