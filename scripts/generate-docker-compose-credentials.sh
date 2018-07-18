#!/usr/bin/env bash
#
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
#

# This script can be used to generate an `.env` for local development with
# docker compose.
#
# Example:
# ./scripts/generate-docker-compose-credentials.sh > .env

source ./scripts/random_string.sh
check_openssl
RET=$?
if [ $RET -eq 1 ]; then
    echo "Please install 'openssl'"
    exit 1
fi

set -Eeo pipefail

cat << EOF
COUCHDB_USER=admin
COUCHDB_PASSWORD=$(gen_random_string)
REDIS_PASSWORD=$(gen_random_string)

KERNEL_ADMIN_USERNAME=admin
KERNEL_ADMIN_PASSWORD=$(gen_random_string)
KERNEL_ADMIN_TOKEN=$(gen_random_string)
KERNEL_DJANGO_SECRET_KEY=$(gen_random_string)
KERNEL_READONLY_DB_USERNAME=readonlyuser
KERNEL_READONLY_DB_PASSWORD=$(gen_random_string)
KERNEL_DB_PASSWORD=$(gen_random_string)

ODK_ADMIN_USERNAME=admin
ODK_ADMIN_PASSWORD=$(gen_random_string)
ODK_ADMIN_TOKEN=$(gen_random_string)
ODK_DJANGO_SECRET_KEY=$(gen_random_string)
ODK_DB_PASSWORD=$(gen_random_string)

COUCHDB_SYNC_ADMIN_USERNAME=admin
COUCHDB_SYNC_ADMIN_PASSWORD=$(gen_random_string)
COUCHDB_SYNC_DJANGO_SECRET_KEY=$(gen_random_string)
COUCHDB_SYNC_DB_PASSWORD=$(gen_random_string)
COUCHDB_SYNC_GOOGLE_CLIENT_ID=$COUCHDB_SYNC_GOOGLE_CLIENT_ID

UI_ADMIN_USERNAME=admin
UI_ADMIN_PASSWORD=$(gen_random_string)
UI_DJANGO_SECRET_KEY=$(gen_random_string)
UI_DB_PASSWORD=$(gen_random_string)
EOF
