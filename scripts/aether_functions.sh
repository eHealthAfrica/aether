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

# Generate credentials if missing
function create_credentials {
    if [ -e ".env" ]; then
        echo "[.env] file already exists! Remove it if you want to generate a new one."
    else
        ./scripts/build_docker_credentials.sh > .env
    fi
}

# Try to create the Aether network+volume if missing
function create_docker_assets {
    ./scripts/build_docker_assets.sh
}

# build Aether client & Aether Common python libraries
function build_libraries_and_distribute {
    ./scripts/build_common_and_distribute.sh
    ./scripts/build_client_and_distribute.sh
}

# build Aether UI assets
function build_ui_assets {
    container=ui-assets

    build_container $container
    docker-compose run $container build
}

# build the indicated container
function build_container {
    container=$1
    APP_REVISION=`git rev-parse --abbrev-ref HEAD`
    if [ ! -f VERSION ]; then
        APP_VERSION="alpha"
    else
        APP_VERSION=`cat ./VERSION`
    fi

    DC="docker-compose -f docker-compose.yml -f docker-compose-connect.yml -f docker-compose-test.yml"

    echo "_____________________________________________ Building container $container"
    $DC build \
        --no-cache --force-rm --pull \
        --build-arg GIT_REVISION=$APP_REVISION \
        --build-arg VERSION=$APP_VERSION \
        $container
}

# upgrade the dependencies of the indicated container
function pip_freeze_container {
    container=$1
    DC="docker-compose -f docker-compose.yml -f docker-compose-connect.yml"

    echo "_____________________________________________ Upgrading container $container"
    $DC run --no-deps $container pip_freeze
}

# kernel readonly user (used by Aether Producer)
function create_readonly_user {
    docker-compose up -d db
    docker-compose run --no-deps kernel setup
    docker-compose run --no-deps kernel eval python /code/sql/create_readonly_user.py
    docker-compose kill
}
