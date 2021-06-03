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

# The purpose of this file is to tell django that there are models linked to
# this module then it runs the `pre_migrate` and `post_migrate` signals,
# otherwise they will be ignored.

from django.db import connection
from django.conf import settings


_DROP_VIEWS = '''
    DROP VIEW IF EXISTS kernel_entity_vw CASCADE;
    DROP VIEW IF EXISTS kernel_schema_vw CASCADE;
    DROP VIEW IF EXISTS multitenancy_mtinstance_vw CASCADE;
'''

_CREATE_MT_VIEW_YES = '''
    CREATE OR REPLACE VIEW multitenancy_mtinstance_vw AS
        SELECT realm, instance_id
        FROM multitenancy_mtinstance
    ;
'''

_CREATE_MT_VIEW_NOT = f'''
    CREATE OR REPLACE VIEW multitenancy_mtinstance_vw AS
        SELECT '{settings.NO_MULTITENANCY_REALM}' AS realm, id AS instance_id
        FROM kernel_project
    ;
'''

_CREATE_SCHEMA_VIEW = '''
    CREATE OR REPLACE VIEW kernel_schema_vw AS
        SELECT
            GREATEST(sd.modified, s.modified) AS modified,

            sd.id                             AS schemadecorator_id,
            sd.name                           AS schemadecorator_name,

            s.id                              AS schema_id,
            s.name                            AS schema_name,
            s.definition                      AS schema_definition,
            s.revision                        AS schema_revision,

            mt.realm                          AS realm,

            (s.family = sd.project_id::text)  AS is_identity

        FROM kernel_schemadecorator           AS sd
        INNER JOIN kernel_schema              AS s
                ON sd.schema_id = s.id
        INNER JOIN kernel_project             AS p
                ON sd.project_id = p.id
               AND p.active IS TRUE
        INNER JOIN multitenancy_mtinstance_vw AS mt
                ON p.id = mt.instance_id
        ORDER BY 1 ASC
    ;
'''

_CREATE_ENTITY_VIEW = '''
    CREATE OR REPLACE VIEW kernel_entity_vw AS
        SELECT
            e.id,
            e.revision,
            e.payload,
            e.modified,
            e.status,

            s.schemadecorator_id,
            s.schemadecorator_name,
            s.schema_name,
            s.schema_id,
            s.schema_revision,
            s.realm

        FROM kernel_entity          AS e
        INNER JOIN kernel_mapping   AS m
                ON e.mapping_id = m.id
               AND m.is_active IS TRUE
        INNER JOIN kernel_schema_vw AS s
                ON e.schemadecorator_id = s.schemadecorator_id
        ORDER BY e.modified ASC
    ;
'''


def pre_migrate_signal(**kwargs):
    with connection.cursor() as cursor:
        cursor.execute(_DROP_VIEWS)


def post_migrate_signal(**kwargs):
    if settings.MULTITENANCY:
        create_sql = _CREATE_MT_VIEW_YES
    else:
        create_sql = _CREATE_MT_VIEW_NOT
    create_sql += _CREATE_SCHEMA_VIEW
    create_sql += _CREATE_ENTITY_VIEW

    with connection.cursor() as cursor:
        cursor.execute(create_sql)
