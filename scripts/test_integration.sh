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
set -e

function build_container() {
    echo "_____________________________________________ Building $1 container"
    $DC_TEST build "$1"-test
}

function prepare_container() {
  echo "_____________________________________________ Preparing $1 container"
  build_container $1
  echo "........"
  $DC_TEST run "$1"-test setup_db
  $DC_TEST run "$1"-test \
           manage setup_admin \
           --username "admin-$1" \
           --password "adminadmin" \
           --token a2d6bc20ad16ec8e715f2f42f54eb00cbbea2d24
  echo "_____________________________________________ $1 ready!"
}

DC_TEST="docker-compose -f docker-compose-test.yml"
DC_COMMON="docker-compose -f docker-compose-common.yml"


echo "_____________________________________________ TESTING"

# kill ALL containers and clean TEST ones
echo "_____________________________________________ Killing ALL containers"
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

echo "_____________________________________________ END"
