#!/usr/bin/env bash
#
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
#

set -Eeuo pipefail

# ensure that the network and volumes were already created
source ./scripts/aether_functions.sh
create_credentials
create_docker_assets

source .env

KC_DB=keycloak
KC_USER=keycloak
KC_URL="http://localhost:8080/auth"

docker-compose kill db keycloak
docker-compose pull db keycloak

echo_message "Starting database server..."
docker-compose up -d db
sleep 5

DB_ID=$(docker-compose ps -q db)
PSQL="docker container exec -i $DB_ID psql"

echo_message "Recreating keycloak database..."
# drops keycloak database (terminating any previous connection) and creates it again
$PSQL <<- EOSQL
    UPDATE pg_database SET datallowconn = 'false' WHERE datname = '${KC_DB}';
    SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${KC_DB}';

    DROP DATABASE ${KC_DB};
    DROP USER ${KC_USER};

    CREATE USER ${KC_USER} PASSWORD '${KEYCLOAK_DB_PASSWORD}';
    CREATE DATABASE ${KC_DB} OWNER ${KC_USER};
EOSQL


echo_message "Starting keycloak server..."

docker-compose up -d keycloak

KC_ID=$(docker-compose ps -q keycloak)
KCADM="docker container exec -i ${KC_ID} ./keycloak/bin/kcadm.sh"

until curl -s ${KC_URL} > /dev/null; do
    >&2 echo_message "Waiting for keycloak server..."
    sleep 2
done

echo_message "Connecting to keycloak server..."
$KCADM \
    config credentials \
    --server ${KC_URL} \
    --realm master \
    --user ${KEYCLOAK_ADMIN_USERNAME} \
    --password ${KEYCLOAK_ADMIN_PASSWORD}

echo_message "Creating default realm ${DEFAULT_REALM}..."
$KCADM \
    create realms \
    -s realm=${DEFAULT_REALM} \
    -s enabled=true

echo_message "Creating default client..."

BASE_URL="http://${NETWORK_DOMAIN}"

# NGINX ports
RU_80="${BASE_URL}/*"
RU_8443="${BASE_URL}:8443/*"
# standalone app ports
RU_8100="${BASE_URL}:8100/*"
RU_8102="${BASE_URL}:8102/*"
RU_8104="${BASE_URL}:8104/*"
RU_8106="${BASE_URL}:8106/*"

$KCADM \
    create clients \
    -r ${DEFAULT_REALM} \
    -s clientId=${KEYCLOAK_AETHER_CLIENT} \
    -s publicClient=true \
    -s directAccessGrantsEnabled=true \
    -s baseUrl="${BASE_URL}" \
    -s 'redirectUris=["'${RU_80}'","'${RU_8443}'","'${RU_8100}'","'${RU_8102}'","'${RU_8104}'","'${RU_8106}'"]' \
    -s enabled=true


echo_message "Creating initial user ${KEYCLOAK_USER_USERNAME}..."
$KCADM \
    create users \
    -r ${DEFAULT_REALM} \
    -s username=${KEYCLOAK_USER_USERNAME} \
    -s enabled=true

echo_message "Setting up initial user password..."
$KCADM \
    set-password \
    -r ${DEFAULT_REALM} \
    --username ${KEYCLOAK_USER_USERNAME} \
    --new-password=${KEYCLOAK_USER_PASSWORD}

echo_message "Done!"

docker-compose kill db keycloak
