#!/usr/bin/env python

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

'''
Create a readonly user in the kernel database.

Background: aether producers can query the kernel database via psycopg2,
bypassing the safety checks django provides. They only need read permissions
and should therefore use a readonly user.

This script is intended to run in the `setup_db` block of `entrypoint.sh`, with
access to all environment variables available in that context.
'''

import os
import logging
import psycopg2
import sys

from psycopg2 import sql

DEBUG = os.environ.get('DEBUG')
LEVEL = logging.DEBUG if DEBUG else logging.WARNING

logging.basicConfig(level=LEVEL)
logger = logging.getLogger(__name__)

# Create a readonly user with username "{role_id}" if none exists.
# Grant read permission for relevant tables.


def main(ro_user, ro_password):
    dbname = os.environ['DB_NAME']
    host = os.environ['PGHOST']
    port = os.environ['PGPORT']
    root_user = os.environ['PGUSER']
    root_password = os.environ['PGPASSWORD']

    logger.debug('db://{user}:{pwrd}@{host}:{port}/{dbname}'.format(
        user=root_user,
        pwrd=(len(root_password) * '*'),
        host=host,
        port=port,
        dbname=dbname,
    ))
    postgres_credentials = {
        'dbname': dbname,
        'host': host,
        'port': port,
        'user': root_user,
        'password': root_password,
    }
    with open('/code/sql/query.sql', 'r') as fp:
        CREATE_READONLY_USER = fp.read()

    with psycopg2.connect(**postgres_credentials) as conn:
        cursor = conn.cursor()
        query = sql.SQL(CREATE_READONLY_USER).format(
            database=sql.Identifier(dbname),
            role_id=sql.Identifier(ro_user),
            role_literal=sql.Literal(ro_user),
            password=sql.Literal(ro_password),
        )
        cursor.execute(query)


if __name__ == '__main__':
    try:
        args = sys.argv[1:]
        main(*args)
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)
