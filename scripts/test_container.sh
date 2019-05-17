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
    LINE=`printf -v row "%${COLUMNS:-$(tput cols)}s"; echo ${row// /=}`

    if [ -z "$1" ]; then
        echo "$LINE"
    else
        msg=" $1 "
        echo "${LINE:${#msg}}$msg"
    fi
}

function build_container {
    echo_message "Building $1 container"
    $DC_TEST build $BUILD_OPTIONS "$1"-test
}

function wait_for_kernel {
    KERNEL_HEALTH_URL="http://localhost:9100/health"
    until curl -s $KERNEL_HEALTH_URL > /dev/null; do
        >&2 echo_message "Waiting for Kernel..."
        sleep 2
    done
}

function wait_for_db {
    until $DC_TEST run kernel-test eval pg_isready -q; do
        >&2 echo_message "Waiting for db-test..."
        sleep 2
    done
}

DC_TEST="docker-compose -f docker-compose-test.yml"
BUILD_OPTIONS="${BUILD_OPTIONS:-}"

./scripts/kill_all.sh

if [[ $1 == "ui" ]]
then
    build_container ui-assets
    $DC_TEST run ui-assets-test test
    $DC_TEST run ui-assets-test build
    echo_message "Tested and built ui assets"
fi


echo_message "Starting databases + Minio Storage server"
$DC_TEST up -d db-test minio-test
if [[ $1 = "couchdb-sync" ]]
then
    $DC_TEST up -d couchdb-test redis-test
fi
if [[ $1 = "integration" ]]
then
    echo_message "Starting Zookeeper and Kafka"
    $DC_TEST up -d zookeeper-test kafka-test
fi


if [[ $1 != "kernel" ]]
then
    # rename kernel test database in each case
    export TEST_KERNEL_DB_NAME=test-kernel-"$1"-$(date "+%Y%m%d%H%M%S")

    build_container kernel

    echo_message "Starting kernel"
    wait_for_db
    $DC_TEST up -d kernel-test
    wait_for_kernel
    echo_message "kernel ready!"

    # Producer and Integration need readonlyuser to be present
    if [[ $1 = "producer" || $1 == "integration" ]]
    then
        echo_message "Creating readonlyuser on Kernel DB"
        $DC_TEST run kernel-test eval python /code/sql/create_readonly_user.py

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
wait_for_db
$DC_TEST run "$1"-test test
echo_message "$1 tests passed!"


./scripts/kill_all.sh
