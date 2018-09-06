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

'''
Create a readonly user in the kernel database.

Background: aether producers can query the kernel database via psycopg2,
bypassing the safety checks django provides. They only need read permissions
and should therefore use a readonly user.

This script is intended to run in the `setup_db` block of `entrypoint.sh`, with
access to all environment variables available in that context.
'''

import os
import psycopg2
from psycopg2 import sql

# Create a readonly user with username "{role_id}" if none exists.
# Grant read permission for relevant tables.
CREATE_READONLY_USER = '''
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = {role_literal})
  THEN
      CREATE ROLE {role_id} WITH LOGIN ENCRYPTED PASSWORD {password}
      INHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
  END IF;
END
$$ LANGUAGE plpgsql;

REVOKE ALL PRIVILEGES ON DATABASE {database} FROM {role_id} CASCADE;

GRANT CONNECT ON DATABASE {database} TO {role_id};
GRANT USAGE ON SCHEMA public TO {role_id};
GRANT SELECT ON kernel_entity TO {role_id};
GRANT SELECT ON kernel_mapping TO {role_id};
GRANT SELECT ON kernel_projectschema TO {role_id};
GRANT SELECT ON kernel_schema TO {role_id};
'''


def main():
    dbname = os.environ['DB_NAME']
    host = os.environ['PGHOST']
    port = os.environ['PGPORT']
    root_user = os.environ['PGUSER']
    root_password = os.environ['PGPASSWORD']

    postgres_credentials = {
        'dbname': dbname,
        'host': host,
        'port': port,
        'user': root_user,
        'password': root_password,
    }

    with psycopg2.connect(**postgres_credentials) as conn:
        ro_user = os.environ['KERNEL_READONLY_DB_USERNAME']
        ro_password = os.environ['KERNEL_READONLY_DB_PASSWORD']
        cursor = conn.cursor()
        query = sql.SQL(CREATE_READONLY_USER).format(
            database=sql.Identifier(dbname),
            role_id=sql.Identifier(ro_user),
            role_literal=sql.Literal(ro_user),
            password=sql.Literal(ro_password),
        )
        cursor.execute(query)


if __name__ == '__main__':
    main()
