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
set -Eeuox pipefail

function kill_all() {
  echo "_____________________________________________ Killing containers"
  ./scripts/kill_all.sh
  $DC_TEST down
}

function build_container() {
  echo "_____________________________________________ Building $1 container"
  $DC_TEST build "$1"-test
}

function prepare_container() {
  echo "_____________________________________________ Preparing $1 container"
  build_container $1
  echo "_____________________________________________ $1 ready!"
}

function prepare_and_test_container() {
  echo "_____________________________________________ Starting $1 tasks"
  prepare_container $1
  $DC_TEST run "$1"-test test
  echo "_____________________________________________ $1 tasks done"
}

DC_TEST="docker-compose -f docker-compose-test.yml"

echo "_____________________________________________ TESTING"

kill_all


echo "_____________________________________________ Common module"
./scripts/build_common_and_distribute.sh

echo "_____________________________________________ Aether utils"
./scripts/build_aether_utils_and_distribute.sh

echo "_____________________________________________ Starting database"
$DC_TEST up -d db-test

# test and start a clean KERNEL TEST container
prepare_and_test_container kernel

echo "_____________________________________________ Starting kernel"
$DC_TEST up -d kernel-test

# test a clean CLIENT TEST container
$DC_TEST build client-test
$DC_TEST run client-test test --noinput

# test a clean ODK TEST container
prepare_and_test_container odk

# test a clean UI TEST container
$DC_TEST build ui-assets-test
$DC_TEST run   ui-assets-test test
$DC_TEST run   ui-assets-test build
prepare_and_test_container ui

echo "_____________________________________________ Starting auxiliary databases"
$DC_TEST up -d couchdb-test redis-test

echo "_____________________________________________ Loading test project in kernel"
$DC_TEST run kernel-test manage loaddata aether/kernel/api/tests/fixtures/project.json

# test a clean SYNC TEST container
prepare_and_test_container couchdb-sync

# clean start for the next bunch of tests
kill_all

# execute INTEGRATION TEST
./scripts/test_integration.sh

echo "_____________________________________________ END"
