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
from producer.settings import SETTINGS
from producer.kernel import KernelClient, logger


_SCHEMAS_SQL = '''
    SELECT schema_id, schema_name, schema_definition, realm
      FROM kernel_schema_vw
'''

_CHECK_UPDATES_SQL = '''
    SELECT id
      FROM kernel_entity_vw
     WHERE modified  > {modified}
       AND schema_id = {schema}
       AND realm     = {realm}
     LIMIT 1;
'''

_COUNT_UPDATES_SQL = '''
    SELECT COUNT(id)
      FROM kernel_entity_vw
     WHERE schema_id = {schema}
       AND realm     = {realm};
'''
_COUNT_MODIFIED_UPDATES_SQL = '''
    SELECT COUNT(id)
      FROM kernel_entity_vw
     WHERE modified  > {modified}
       AND schema_id = {schema}
       AND realm     = {realm};
'''

_GET_UPDATES_SQL = '''
    SELECT *
      FROM kernel_entity_vw
     WHERE modified  > {modified}
       AND schema_id = {schema}
       AND realm     = {realm}
     ORDER BY modified ASC
     LIMIT {limit};
'''


class KernelDBClient(KernelClient):

    def __init__(self):
        super(KernelDBClient, self).__init__()

        pg_requires = ['user', 'dbname', 'port', 'host', 'password']
        pg_creds = {key: SETTINGS.get_required(f'postgres_{key}') for key in pg_requires}
        kernel_db_pool_size = int(SETTINGS.get('kernel_db_pool_size', 6))
        self.pool = PriorityDatabasePool(pg_creds, 'KernelDBClient', kernel_db_pool_size)

    def mode(self):
        return 'db'

    def get_schemas(self):
        self.last_check = datetime.now().isoformat()
        name = 'schemas_query'
        query = sql.SQL(_SCHEMAS_SQL)
        cursor = self._exec_sql(name, 1, query)
        if cursor:
            self.last_check_error = None
            for row in cursor:
                yield {key: row[key] for key in row.keys()}
        else:
            self.last_check_error = 'Could not access kernel database to get topics'
            logger.critical('Could not access kernel database to get topics')
            return []

    def check_updates(self, realm, schema_id, schema_name, modified):
        query = sql.SQL(_CHECK_UPDATES_SQL).format(
            modified=sql.Literal(modified),
            schema=sql.Literal(schema_id),
            realm=sql.Literal(realm),
        )
        cursor = self._exec_sql(schema_name, 1, query)
        if cursor:
            return sum([1 for i in cursor]) > 0
        else:
            logger.critical('Could not access kernel database to look for updates')
            return False

    def count_updates(self, realm, schema_id, schema_name, modified=''):
        if modified:
            query = sql.SQL(_COUNT_MODIFIED_UPDATES_SQL).format(
                modified=sql.Literal(modified),
                schema=sql.Literal(schema_id),
                realm=sql.Literal(realm),
            )
        else:
            query = sql.SQL(_COUNT_UPDATES_SQL).format(
                schema=sql.Literal(schema_id),
                realm=sql.Literal(realm),
            )
        cursor = self._exec_sql(schema_name, 0, query)
        if cursor:
            _count = cursor.fetchone()[0]
            logger.debug(f'Reporting requested size for {schema_name} of {_count}')
            return {'count': _count}
        else:
            logger.critical('Could not access kernel database to look for updates')
            return -1

    def get_updates(self, realm, schema_id, schema_name, modified):
        query = sql.SQL(_GET_UPDATES_SQL).format(
            modified=sql.Literal(modified),
            schema=sql.Literal(schema_id),
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
            logger.critical('Could not access kernel database to look for updates')
            return []

    def _exec_sql(self, name, priority, query):
        try:
            promise = self.pool.request_connection(priority, name)
            conn = promise.get()
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(query)

            return cursor

        except psycopg2.OperationalError as pgerr:
            logger.critical(f'Error while accessing database: {pgerr}')
            logger.exception(pgerr)
            return None

        finally:
            try:
                self.pool.release(name, conn)
            except UnboundLocalError:
                logger.error(f'{name} could not release a connection it never received.')
