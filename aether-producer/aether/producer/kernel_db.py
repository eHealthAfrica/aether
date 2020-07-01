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

import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor

from aether.producer.db import PriorityDatabasePool
from aether.producer.settings import SETTINGS
from aether.producer.kernel import KernelClient, logger
from aether.producer.utils import utf8size


_REALMS_SQL = '''
    SELECT DISTINCT ON (realm) realm
      FROM kernel_schema_vw
'''

_SCHEMAS_SQL_ALL_REALMS = '''
    SELECT schema_id, schema_name, schema_definition, realm
      FROM kernel_schema_vw
'''

_SCHEMAS_SQL_SINGLE_REALM = _SCHEMAS_SQL_ALL_REALMS + '''
     WHERE realm     = {realm};'''


__CHECK_UPDATES_SQL = '''
    SELECT id
      FROM kernel_entity_vw
     WHERE modified  > {modified}
       AND realm     = {realm}
'''

_CHECK_UPDATES_SQL_SINGLE = __CHECK_UPDATES_SQL + '''
       AND schema_id = {schema}
     LIMIT 1;
'''

_CHECK_UPDATES_SQL_ALL = __CHECK_UPDATES_SQL + '''
     LIMIT 1;
'''

__COUNT_UPDATES_SQL = '''
    SELECT COUNT(id)
      FROM kernel_entity_vw
     WHERE realm     = {realm}'''

_COUNT_UPDATES_SQL_SINGLE = __COUNT_UPDATES_SQL + '''
       AND schema_id = {schema};
'''

_COUNT_UPDATES_SQL_ALL = __COUNT_UPDATES_SQL + ';'

__COUNT_MODIFIED_UPDATES_SQL = '''
    SELECT COUNT(id)
      FROM kernel_entity_vw
     WHERE modified  > {modified}
       AND realm     = {realm}'''

_COUNT_MODIFIED_UPDATES_SQL_ALL = __COUNT_MODIFIED_UPDATES_SQL + ';'

_COUNT_MODIFIED_UPDATES_SQL_SINGLE = __COUNT_MODIFIED_UPDATES_SQL + '''
       AND schema_id = {schema};
'''

__GET_UPDATES_SQL = '''
    SELECT *
      FROM kernel_entity_vw
     WHERE modified  > {modified}
       AND realm     = {realm}
'''

_GET_UPDATES_SQL_ALL = __GET_UPDATES_SQL + '''
     ORDER BY modified ASC
     LIMIT {limit};
'''

_GET_UPDATES_SQL_SINGLE = __GET_UPDATES_SQL + '''
       AND schema_id = {schema}
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

    def get_realms(self):
        query = sql.SQL(_REALMS_SQL)
        cursor = self._exec_sql('get_realms', 1, query)
        return [row['realm'] for row in cursor]

    def get_schemas(self, realm=None):
        self.last_check = datetime.now().isoformat()
        name = 'schemas_query'
        if realm:
            query = sql.SQL(_SCHEMAS_SQL_SINGLE_REALM).format(realm=sql.Literal(realm))
        else:
            query = sql.SQL(_SCHEMAS_SQL_ALL_REALMS)
        cursor = self._exec_sql(name, 1, query)
        if cursor:
            self.last_check_error = None
            for row in cursor:
                yield {key: row[key] for key in row.keys()}
        else:
            self.last_check_error = 'Could not access kernel database to get topics'
            logger.warning('Could not access kernel database to get topics')
            return []

    def check_updates(self, realm, schema_id=None, schema_name=None, modified=''):
        if schema_id:
            query = sql.SQL(_CHECK_UPDATES_SQL_SINGLE).format(
                modified=sql.Literal(modified),
                schema=sql.Literal(schema_id),
                realm=sql.Literal(realm),
            )
        else:
            query = sql.SQL(_CHECK_UPDATES_SQL_ALL).format(
                modified=sql.Literal(modified),
                realm=sql.Literal(realm),
            )
        cursor = self._exec_sql(schema_name or 'All', 1, query)
        if cursor:
            return sum([1 for i in cursor]) > 0
        else:
            logger.warning('Could not access kernel database to look for updates')
            return False

    def count_updates(self, realm, schema_id=None, schema_name=None, modified=''):
        if modified:
            if schema_id:
                query = sql.SQL(_COUNT_MODIFIED_UPDATES_SQL_SINGLE).format(
                    modified=sql.Literal(modified),
                    schema=sql.Literal(schema_id),
                    realm=sql.Literal(realm),
                )
            else:
                query = sql.SQL(_COUNT_MODIFIED_UPDATES_SQL_ALL).format(
                    modified=sql.Literal(modified),
                    realm=sql.Literal(realm),
                )

        else:
            if schema_id:
                query = sql.SQL(_COUNT_UPDATES_SQL_SINGLE).format(
                    schema=sql.Literal(schema_id),
                    realm=sql.Literal(realm),
                )
            else:
                query = sql.SQL(_COUNT_UPDATES_SQL_ALL).format(
                    realm=sql.Literal(realm),
                )
        cursor = self._exec_sql(schema_name or 'All', 0, query)
        if cursor:
            _count = cursor.fetchone()[0]
            logger.debug(f'Reporting requested size for {schema_name or "All"} of {_count}')
            return {'count': _count}
        else:
            logger.warning('Could not access kernel database to look for updates')
            return -1

    def get_updates(self, realm, schema_id=None, schema_name=None, modified=''):
        if schema_id:
            query = sql.SQL(_GET_UPDATES_SQL_SINGLE).format(
                modified=sql.Literal(modified),
                schema=sql.Literal(schema_id),
                realm=sql.Literal(realm),
                limit=sql.Literal(self.limit),
            )
        else:
            query = sql.SQL(_GET_UPDATES_SQL_ALL).format(
                modified=sql.Literal(modified),
                realm=sql.Literal(realm),
                limit=sql.Literal(self.limit),
            )

        query_time = datetime.now()
        cursor = self._exec_sql(schema_name or 'All', 2, query)
        if cursor:
            window_filter = self.get_time_window_filter(query_time)

            res = []
            size = 0
            for row in cursor:
                if window_filter(row):
                    entry = {key: row[key] for key in row.keys()}
                    new_size = size + utf8size(entry)
                    res.append(entry)
                    if new_size >= self.batch_size:
                        # when we get over the batch size, truncate
                        # this means even with a batch size of 1, if a message
                        # is 10, we still emit one message
                        return res
                    size = new_size

            return res

        else:
            logger.warning('Could not access kernel database to look for updates')
            return []

    def _exec_sql(self, name, priority, query):
        try:
            promise = self.pool.request_connection(priority, name)
            conn = promise.get()
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(query)

            return cursor

        except psycopg2.OperationalError as pgerr:
            logger.warning(f'Error while accessing database: {pgerr}')
            logger.debug(pgerr)
            return None

        finally:
            try:
                self.pool.release(name, conn)
            except UnboundLocalError:
                logger.warning(f'{name} could not release a connection it never received.')
