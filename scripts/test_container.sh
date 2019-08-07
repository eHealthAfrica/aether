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
    local LINE=`printf -v row "%${COLUMNS:-$(tput cols)}s"; echo ${row// /=}`

    if [ -z "$1" ]; then
        echo "$LINE"
    else
        msg=" $1 "
        echo "${LINE:${#msg}}$msg"
    fi
}

function build_container {
    echo_message "Building $1 container"

    $DC_TEST build $BUILD_OPTIONS \
        --build-arg GIT_REVISION=$APP_REVISION \
        --build-arg VERSION=$APP_VERSION \
        "$1"-test
}


function _wait_for {
    local container=$1
    local is_ready=$2

    echo_message "Starting $container..."
    $DC_TEST up -d "${container}-test"

    local retries=1
    until $is_ready > /dev/null; do
        >&2 echo "Waiting for $container... $retries"
        sleep 2

        ((retries++))
        if [[ $retries -gt 30 ]]; then
            echo_message "It was not possible to start $container"
            exit 1
        fi
    done
    echo_message "$container is ready!"
}

function start_database_test {
    _wait_for "db" "$DC_KERNEL_RUN eval pg_isready -q"
}

function start_kernel_test {
    start_database_test
    _wait_for "kernel" "$DC_KERNEL_RUN manage check_url -u $KERNEL_HEALTH_URL"
}

function kill_test {
    $DC_TEST kill     2> /dev/null || true
    $DC_TEST down -v  2> /dev/null || true
}

# TEST environment
DC_TEST="docker-compose -f docker-compose-test.yml"
DC_KERNEL_RUN="$DC_TEST run --rm kernel-test"
KERNEL_HEALTH_URL="http://kernel-test:9100/health"

BUILD_OPTIONS="${BUILD_OPTIONS:-}"
APP_VERSION=$(date "+%Y%m%d%H%M%S")
APP_REVISION=`git rev-parse --abbrev-ref HEAD`

kill_test

if [[ $1 == "ui" ]]; then
    build_container ui-assets
    $DC_TEST run --rm ui-assets-test test
    $DC_TEST run --rm ui-assets-test build
    echo_message "Tested and built ui assets"
fi


echo_message "Starting databases + Minio Storage server"
$DC_TEST up -d db-test minio-test
if [[ $1 = "couchdb-sync" ]]; then
    $DC_TEST up -d couchdb-test redis-test
fi
if [[ $1 = "integration" ]]; then
    echo_message "Starting Zookeeper and Kafka"
    $DC_TEST up -d zookeeper-test kafka-test
fi


if [[ $1 != "kernel" ]]; then
    # rename kernel test database in each case
    export TEST_KERNEL_DB_NAME=test-kernel-"$1"-$(date "+%Y%m%d%H%M%S")

    build_container kernel
    start_kernel_test

    # Producer and Integration need readonlyuser to be present
    if [[ $1 = "producer" || $1 == "integration" ]]; then
        echo_message "Creating readonlyuser on Kernel DB"
        $DC_KERNEL_RUN eval python /code/sql/create_readonly_user.py

        if [[ $1 = "integration" ]]
        then
            build_container producer
            echo_message "Starting producer"
            $DC_TEST up -d producer-test
            echo_message "producer ready!"
        fi
    fi
fi


echo_message "Preparing $1 container"
build_container $1
echo_message "$1 ready!"
start_database_test
$DC_TEST run --rm "$1"-test test
echo_message "$1 tests passed!"


kill_test
