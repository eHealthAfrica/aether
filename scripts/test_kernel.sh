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
  echo "_________________________________________________ Preparing $1 container"
  build_container $1
  $DC_TEST run "$1"-test setuplocaldb
  echo "_________________________________________________ $1 ready!"
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

# test and start a clean KERNEL TEST container
prepare_and_test_container kernel

echo "_____________________________________________ Starting kernel"
$DC_TEST up -d kernel-test

# kill ALL containers
echo "_____________________________________________ Killing auxiliary containers"
./scripts/kill_all.sh

echo "_____________________________________________ END"
