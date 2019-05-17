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

source .env

# recreate network
docker network rm ${NETWORK_NAME} || true
{
    docker network create ${NETWORK_NAME} \
        --attachable \
        --subnet=${NETWORK_SUBNET} \
        --gateway=${NETWORK_GATEWAY}
} || true
echo "${NETWORK_NAME} network is ready."


# check that the volume exists or create it
docker volume create ${DB_VOLUME} || true
echo "${DB_VOLUME} volume is ready."

# refresh the docker images
docker-compose pull db nginx redis couchdb minio
