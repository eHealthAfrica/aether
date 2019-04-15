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

KC_DB=keycloak
KC_USER=keycloak
KC_URL="http://localhost:8080/auth"
LINE="_____________________________________________"

# ensure that the network and volumes were already created
./scripts/build_docker_assets.sh

docker-compose kill db keycloak
docker-compose pull db keycloak

echo "${LINE} Starting database server..."
docker-compose up -d db
sleep 5

DB_ID=$(docker-compose ps -q db)
PSQL="docker container exec -i $DB_ID psql"

echo "${LINE} Recreating keycloak database..."
# drops keycloak database (terminating any previous connection) and creates it again
$PSQL <<- EOSQL
    UPDATE pg_database SET datallowconn = 'false' WHERE datname = '${KC_DB}';
    SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${KC_DB}';

    DROP DATABASE ${KC_DB};
    DROP USER ${KC_USER};

    CREATE USER ${KC_USER} PASSWORD '${KEYCLOAK_DB_PASSWORD}';
    CREATE DATABASE ${KC_DB} OWNER ${KC_USER};
EOSQL


echo "${LINE} Starting keycloak server..."

docker-compose up -d keycloak

KC_ID=$(docker-compose ps -q keycloak)
KCADM="docker container exec -i ${KC_ID} ./keycloak/bin/kcadm.sh"

until curl -s ${KC_URL} > /dev/null; do
    >&2 echo "${LINE} Waiting for keycloak server..."
    sleep 2
done

echo "${LINE} Connecting to keycloak server..."
$KCADM \
    config credentials \
    --server ${KC_URL} \
    --realm master \
    --user ${KEYCLOAK_ADMIN_USERNAME} \
    --password ${KEYCLOAK_ADMIN_PASSWORD}

echo "${LINE} Creating default realm ${DEFAULT_REALM}..."
$KCADM \
    create realms \
    -s realm=${DEFAULT_REALM} \
    -s enabled=true

echo "${LINE} Creating default clients..."
CLIENTS=( kernel odk sync ui )
for CLIENT in "${CLIENTS[@]}"
do
    CLIENT_URL="http://${NETWORK_DOMAIN}/${CLIENT}"
    REDIRECT_URI_80="${CLIENT_URL}/accounts/login/"
    # required by ODK Collect
    REDIRECT_URI_8443="http://${NETWORK_DOMAIN}:8443/${CLIENT}/accounts/login/"

    echo "${LINE} Creating client ${CLIENT}..."
    $KCADM \
        create clients \
        -r ${DEFAULT_REALM} \
        -s clientId=${CLIENT} \
        -s publicClient=true \
        -s directAccessGrantsEnabled=true \
        -s baseUrl=${CLIENT_URL} \
        -s 'redirectUris=["'${REDIRECT_URI_80}'","'${REDIRECT_URI_8443}'"]' \
        -s enabled=true
done

echo "${LINE} Creating initial user ${KEYCLOAK_USER_USERNAME}..."
$KCADM \
    create users \
    -r ${DEFAULT_REALM} \
    -s username=${KEYCLOAK_USER_USERNAME} \
    -s enabled=true

echo "${LINE} Setting up initial user password..."
$KCADM \
    set-password \
    -r ${DEFAULT_REALM} \
    --username ${KEYCLOAK_USER_USERNAME} \
    --new-password=${KEYCLOAK_USER_PASSWORD}

echo "${LINE} Done!"

docker-compose kill db keycloak
