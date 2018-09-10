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

# Generate credentials if missing
if [ -e ".env" ]; then
    echo "[.env] file already exists! Remove it if you want to generate a new one."
else
    ./scripts/generate-docker-compose-credentials.sh > .env
fi

set -Eeuo pipefail

# Try to create the Aether network+volume if missing
docker network create aether_internal       2>/dev/null || true
docker volume  create aether_database_data  2>/dev/null || true

# build Aether utilities
./scripts/build_aether_utils_and_distribute.sh

# build Aether Connect
docker-compose -f docker-compose-connect.yml build

# build Aether Common python module
./scripts/build_common_and_distribute.sh

# build Aether UI assets
docker-compose build ui-assets
docker-compose run   ui-assets build

VERSION=`git rev-parse --abbrev-ref HEAD`
GIT_REVISION=`git rev-parse HEAD`
CONTAINERS=( kernel ui odk couchdb-sync )

# speed up first start up
docker-compose up -d db

# build Aether Suite
for container in "${CONTAINERS[@]}"
do
    # build container
    docker-compose build \
        --build-arg GIT_REVISION=$GIT_REVISION \
        --build-arg VERSION=$VERSION \
        $container

    # setup container (model migration, admin user, static content...)
    docker-compose run $container setup
done

# kernel readonly user (used by Aether Producer)
docker-compose run kernel eval python /code/sql/create_readonly_user.py

docker-compose kill
