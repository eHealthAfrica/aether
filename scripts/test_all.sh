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
# software distributed under the License is distributed on anx
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
set -Eeuox pipefail

function prepare_and_test_container() {
  container="$1"-test

  echo "_____________________________________________ Starting $1 tasks"
  $DC_TEST build $container
  $DC_TEST run   $container setuplocaldb
  $DC_TEST run $container test --noinput
  echo "_____________________________________________ $1 tasks done"
}

function prepare_and_test_container_load_kernel_data() {
    container="$1"-test

    echo "_____________________________________________ Starting $1 tasks"
    $DC_TEST build $container
    $DC_TEST run   $container setuplocaldb
    $DC_TEST run kernel-test manage loaddata $2
    $DC_TEST run $container test --noinput
    echo "_____________________________________________ $1 tasks done"
}

function prepare_container() {
  echo "_____________________________________________ Preparing $1 container"
  build_container $1
  $DC_TEST run "$1"-test setuplocaldb
  echo "_____________________________________________ $1 ready!"
}

function build_container() {
  echo "_____________________________________________ Building $1 container"
  $DC_TEST build "$1"-test

}

function build_container() {
  echo "_________________________________________________ Building $1 container"
  $DC_TEST build "$1"-test

}

DC_TEST="docker-compose -f docker-compose-test.yml"
DC_COMMON="docker-compose -f docker-compose-common.yml"

echo "_____________________________________________ TESTING"

# kill ALL containers and clean TEST ones
echo "_____________________________________________ Killing ALL containers"
./scripts/kill_all.sh
$DC_TEST down

echo "_____________________________________________ Testing common module"
$DC_COMMON down
$DC_COMMON build
$DC_COMMON run common test

# start databases
echo "_____________________________________________ Starting databases"
$DC_TEST up -d db-test couchdb-test redis-test

# test and start a clean KERNEL TEST container
prepare_and_test_container kernel

echo "_____________________________________________ Starting kernel"
$DC_TEST up -d kernel-test

# test a clean CLIENT TEST container
prepare_and_test_container client

# test and start a clean ODK TEST container
prepare_and_test_container_load_kernel_data odk aether/kernel/api/tests/fixtures/project_empty_schema.json

# test a clean SYNC TEST container
prepare_and_test_container_load_kernel_data couchdb-sync aether/kernel/api/tests/fixtures/project.json

# test a clean UI TEST container
prepare_and_test_container ui

# kill ALL containers
echo "_____________________________________________ Killing auxiliary containers"
./scripts/kill_all.sh
$DC_TEST down

# start databases
echo "_____________________________________________ Starting database"
$DC_TEST up -d db-test

# start a clean KERNEL TEST container
prepare_container kernel

echo "_____________________________________________ Starting kernel"
$DC_TEST up -d kernel-test

build_container kafka
build_container zookeeper
echo "_____________________________________________ Starting Kafka"
$DC_TEST up -d zookeeper-test kafka-test

build_container producer
echo "_____________________________________________ Starting Producer"
$DC_TEST up -d producer-test

# test a clean INGEGRATION TEST container
echo "_____________________________________________ Starting Integration Tests"
build_container integration
$DC_TEST run integration-test test

# kill ALL containers
echo "_____________________________________________ Killing auxiliary containers"
./scripts/kill_all.sh
$DC_TEST down

# start databases
echo "_____________________________________________ Starting database"
$DC_TEST up -d db-test

# start a clean KERNEL TEST container
prepare_container kernel

echo "_____________________________________________ Starting kernel"
$DC_TEST up -d kernel-test

build_container kafka
build_container zookeeper
echo "_____________________________________________ Starting Kafka"
$DC_TEST up -d zookeeper-test kafka-test

build_container producer
echo "_____________________________________________ Starting Producer"
$DC_TEST up -d producer-test

# test a clean INTEGRATION TEST container
echo "_____________________________________________ Starting Integration Tests"
build_container integration
$DC_TEST run integration-test test

# kill ALL containers
echo "_____________________________________________ Killing auxiliary containers"
./scripts/kill_all.sh

# Testing Consumer Library
./scripts/test_consumer_lib.sh

echo "_____________________________________________ END"
