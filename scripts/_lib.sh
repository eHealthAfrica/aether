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

function echo_message {
    local LINE=`printf -v row "%${COLUMNS:-$(tput cols)}s"; echo ${row// /_}`

    if [ -z "$1" ]; then
        echo "$LINE"
    else
        local msg=" $1 "
        echo "${LINE:${#msg}}$msg"
    fi
}

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

# build Aether client python library
function build_client {
    ./scripts/build_client_and_distribute.sh
}

# build Aether UI assets
function build_ui_assets {
    local container=ui-assets

    build_container $container
    docker-compose run --rm $container build
}

# build the indicated container
function build_container {
    local container=$1
    local APP_REVISION=`git rev-parse --abbrev-ref HEAD`
    if [ ! -f VERSION ]; then
        local APP_VERSION="0.0.0"
    else
        local APP_VERSION=`cat ./VERSION`
    fi

    local DC="docker-compose -f docker-compose.yml -f docker-compose-connect.yml -f docker-compose-test.yml"

    echo_message "Building container $container"
    $DC build \
        --no-cache --force-rm --pull \
        --build-arg GIT_REVISION=$APP_REVISION \
        --build-arg VERSION=$APP_VERSION \
        $container
}

# build the container and tag it as local
function build_local {
    local container=$1
    local APP_REVISION=`git rev-parse --abbrev-ref HEAD`
    local DC="docker-compose -f docker-compose.yml -f docker-compose-connect.yml -f docker-compose-test.yml"

    echo_message "Building local container $container"
    $DC build \
        --build-arg GIT_REVISION=$APP_REVISION \
        --build-arg VERSION=local \
        $container
    docker tag aether-$container:latest aether-$container:local
}

# upgrade the dependencies of the indicated container
function pip_freeze_container {
    local container=$1
    local DC="docker-compose -f docker-compose.yml -f docker-compose-connect.yml"

    echo_message "Upgrading container $container"
    $DC run --rm --no-deps $container pip_freeze
}

# kernel readonly user (used by Aether Producer)
# Usage:    create_readonly_user <db-user-name> <db-user-password>
function create_readonly_user {
    docker-compose up -d db
    docker-compose run --rm --no-deps kernel setup
    docker-compose run --rm --no-deps kernel eval \
        python3 /code/sql/create_readonly_user.py "$1" "$2"
    docker-compose kill
}

# Start database container and wait till is up and responding
function start_db {
    _wait_for "db" "docker-compose run --rm --no-deps kernel eval pg_isready -q"
}

# Start container and wait till is up and responding
# Usage:    start_container <container-name> <container-health-url>
function start_container {
    local container=$1
    local is_ready="docker-compose run --rm --no-deps kernel manage check_url -u $2"

    _wait_for "$container" "$is_ready"
}

function _wait_for {
    local container=$1
    local is_ready=$2

    echo_message "Starting $container server..."
    docker-compose up -d $container

    local retries=1
    until $is_ready > /dev/null; do
        >&2 echo "Waiting for $container... $retries"

        ((retries++))
        if [[ $retries -gt 30 ]]; then
            echo_message "It was not possible to start $container"
            exit 1
        fi

        sleep 2
    done
    echo_message "$container is ready!"
}
