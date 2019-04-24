from datetime import datetime
from typing import (
    List
)
import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor

from producer.db import KERNEL_DB as POSTGRES
from producer.logger import LOG

window_size_sec = 0

# NEW_STR = '''
#         SELECT
#             e.id,
#             e.modified
#         FROM kernel_entity e
#         inner join kernel_schemadecorator ps on e.schemadecorator_id = ps.id
#         inner join kernel_schema s on ps.schema_id = s.id
#         WHERE e.modified > {modified}
#         AND s.name = {schema_name}
#         LIMIT 1; '''

#     # Count how many unique (controlled by kernel) messages should currently be in this topic
#     COUNT_STR = '''
#             SELECT
#                 count(e.id)
#             FROM kernel_entity e
#             inner join kernel_schemadecorator ps on e.schemadecorator_id = ps.id
#             inner join kernel_schema s on ps.schema_id = s.id
#             WHERE s.name = {schema_name};
#     '''

#     # Changes pull query
#     QUERY_STR = '''
#             SELECT
#                 e.id,
#                 e.revision,
#                 e.payload,
#                 e.modified,
#                 e.status,
#                 ps.id as schemadecorator_id,
#                 ps.name as schemadecorator_name,
#                 s.name as schema_name,
#                 s.id as schema_id,
#                 s.revision as schema_revision
#             FROM kernel_entity e
#             inner join kernel_schemadecorator ps on e.schemadecorator_id = ps.id
#             inner join kernel_schema s on ps.schema_id = s.id
#             WHERE e.modified > {modified}
#             AND s.name = {schema_name}
#             ORDER BY e.modified ASC
#             LIMIT {limit};
#         '''

# are there any new entities, regardless of tenant, etc
NEW_STR = '''
        SELECT
            e.id,
            e.modified
        FROM kernel_entity e
        inner join kernel_schemadecorator ps on e.schemadecorator_id = ps.id
        inner join kernel_schema s on ps.schema_id = s.id
        WHERE e.modified > {modified}
        LIMIT 1; '''

# get matching project schemas between start and some end time

# Changes pull query
QUERY_STR = '''
        SELECT
            e.id,
            e.revision,
            e.payload,
            e.modified,
            e.status,
            ps.id as schemadecorator_id,
            ps.name as schemadecorator_name,
            s.name as schema_name,
            s.id as schema_id,
            s.revision as schema_revision,
            mt.realm as realm
        FROM kernel_entity e
        inner join kernel_schemadecorator ps on e.schemadecorator_id = ps.id
        inner join kernel_schema s on ps.schema_id = s.id
        inner join multitenancy_mtinstance mt on e.project_id = mt.instance_id
        WHERE e.modified > {start_modified}
        AND e.modified <= {end_modified}
        AND ps.id in {schemadecorator_ids}  # should be formatted (1, 2, 3)
        ORDER BY e.modified ASC
        LIMIT {limit};  # probably don't need a limit if we're just throwing into Redis
    '''

ALL_ENTITIES_SINCE_STR = '''
        SELECT
            e.id,
            e.revision,
            e.payload,
            e.modified,
            e.status,
            ps.id as schemadecorator_id,
            ps.name as schemadecorator_name,
            s.name as schema_name,
            s.id as schema_id,
            s.revision as schema_revision,
            mt.realm as realm
        FROM kernel_entity e
        inner join kernel_schemadecorator ps on e.schemadecorator_id = ps.id
        inner join kernel_schema s on ps.schema_id = s.id
        inner join multitenancy_mtinstance mt on e.project_id = mt.instance_id
        WHERE e.modified > {modified}
        ORDER BY e.modified ASC
    '''

# Count how many unique (controlled by kernel) messages should currently be in this topic
COUNT_STR = '''
        SELECT
            count(e.id)
        FROM kernel_entity e
        inner join kernel_schemadecorator ps on e.schemadecorator_id = ps.id
        inner join kernel_schema s on ps.schema_id = s.id
        WHERE ps.id in {schemadecorator_ids};
'''
# should be formatted (1, 2, 3)

name = 'test'


def count_entities(decorator_ids: List[str]) -> int:
    query = sql.SQL(COUNT_STR.format(
        schemadecorator_ids=str(tuple(decorator_ids))
    ))
    try:
        # needs to be quick
        promise = POSTGRES.request_connection(0, name)
        conn = promise.get()
        cursor = conn.cursor(cursor_factory=DictCursor)
        cursor.execute(query)
        size = [{key: row[key] for key in row.keys()}
                for row in cursor][0].get('count', 0)
        LOG.debug(
            f'Reporting requested size for {name} of {size}'
        )
        return size
    except psycopg2.OperationalError as pgerr:
        LOG.critical(
            'Could not access db to get topic size: %s' % pgerr)
        return -1
    finally:
        try:
            POSTGRES.release(name, conn)
        except UnboundLocalError:
            LOG.error(
                f'{name} could not release a'
                ' connection it never received.'
            )


def get_all_db_updates(since=''):
    # "" evals to < all strings
    query = sql.SQL(ALL_ENTITIES_SINCE_STR).format(
        modified=sql.Literal(since)
    )
    query_time = datetime.now()

    try:
        promise = POSTGRES.request_connection(2, name)  # Lowest priority
        conn = promise.get()
        cursor = conn.cursor(cursor_factory=DictCursor)
        cursor.execute(query)
        window_filter = get_time_window_filter(query_time)
        for row in cursor:
            if window_filter(row):
                yield {key: row[key] for key in row.keys()}

    except psycopg2.OperationalError as pgerr:
        LOG.critical(
            'Could not access Database to look for updates: %s' % pgerr)
        return []
    finally:
        try:
            POSTGRES.release(name, conn)
        except UnboundLocalError:
            LOG.error(
                f'{name} could not release a'
                ' connection it never received.'
            )


def get_time_window_filter(query_time):
    # You can't always trust that a set from kernel made up of time window
    # start < _time < end is complete if nearlyequal(_time, now()).
    # Sometimes rows belonging to that set would show up a couple mS after
    # the window had closed and be dropped. Our solution was to truncate
    # sets based on the insert time and now() to provide a buffer.
    TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'

    def fn(row):
        commited = datetime.strptime(row.get('modified')[:26], TIME_FORMAT)
        lag_time = (query_time - commited).total_seconds()
        if lag_time > window_size_sec:
            return True
        elif lag_time < -30.0:
            # Sometimes fractional negatives show up. More than 30 seconds
            # is an issue though.
            LOG.critical(
                f'INVALID LAG INTERVAL: {lag_time}.'
                ' Check time settings on server.')
        _id = row.get('id')
        LOG.debug(f'WINDOW EXCLUDE: ID: {_id}, LAG: {lag_time}')
        return False
    return fn

# SELECT MT.realm, E.*
# FROM multitenancy_mtinstance MT
# INNER JOIN kernel_project P
#   ON MT.instance_id = P.id
# INNER JOIN kernel_entity E
#   ON E.project_id = P.id