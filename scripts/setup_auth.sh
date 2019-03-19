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
set -Eeuo pipefail

source .env

DCA="docker-compose -f ./docker-compose-auth.yml"

$DCA kill
$DCA down


# Try to create the Aether network+volume if missing
docker network create aether_internal       2>/dev/null || true
docker volume  create aether_database_data  2>/dev/null || true

./scripts/generate-aether-version-assets.sh
./scripts/build_common_and_distribute.sh

$DCA up -d db
sleep 5

DB_ID=$($DCA ps -q db)

# THESE COMMANDS WILL ERASE PREVIOUS DATA!!!
docker container exec -i $DB_ID psql <<- EOSQL
    DROP DATABASE kong;
    DROP USER kong;

    CREATE USER kong PASSWORD '${KONG_DB_PASSWORD}';
    CREATE DATABASE kong OWNER kong;
EOSQL
docker container exec -i $DB_ID psql <<- EOSQL
    DROP DATABASE keycloak;
    DROP USER keycloak;

    CREATE USER keycloak PASSWORD '${KEYCLOAK_DB_PASSWORD}';
    CREATE DATABASE keycloak OWNER keycloak;
EOSQL

$DCA build auth keycloak kernel

$DCA run kong kong migrations bootstrap 2>/dev/null || :  # bootstrap not in all image versions?
$DCA run kong kong migrations up  # if bootstrap is invalid, only up is required.
sleep 5

$DCA up -d kong keycloak
$DCA logs kong keycloak
sleep 5

$DCA run auth setup_auth

# arguments: client name, client url
$DCA run auth register_app kernel       http://kernel:8000
# $DCA run auth register_app odk          http://odk:8002
# $DCA run auth register_app ui           http://ui:8004
# $DCA run auth register_app couchdb-sync http://couchdb-sync:8006

sleep 5
$DCA run auth make_realm

$DCA kill
