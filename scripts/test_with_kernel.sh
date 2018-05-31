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
set -Eeuo pipefail

function prepare_container() {
  echo "_____________________________________________ Preparing $1 container"
  $DC_TEST build "$1"-test
  $DC_TEST run "$1"-test setuplocaldb
  echo "_____________________________________________ $1 ready!"
}


if [ -n "$1" ];
then
  # take container name from argument, expected values `odk` or `couchdb-sync`
  echo "Executing tests for $1 container"
  container=$1
else
  echo "Nothing to do."
  exit 0
fi

DC_TEST="docker-compose -f docker-compose-test.yml"

# make sure that there is nothing up before starting
echo "_____________________________________________ Killing ALL containers"
./scripts/kill_all.sh
$DC_TEST down


echo "_____________________________________________ Starting databases"
$DC_TEST up -d db-test
if [[ $container = "couchdb-sync" ]]
then
  $DC_TEST up -d couchdb-test redis-test
fi

# prepare and start KERNEL container
prepare_container kernel

echo "_____________________________________________ Starting kernel"
$DC_TEST up -d kernel-test
if [[ $container == "couchdb-sync" ]]
then
  fixture=aether/kernel/api/tests/fixtures/project.json
  $DC_TEST run kernel-test manage loaddata $fixture
  echo "_____________________________________________ Loaded initial data in kernel"
fi


# build test container
prepare_container $container

echo "_____________________________________________ Testing $container"
$DC_TEST run "$container"-test test


echo "_____________________________________________ Killing ALL containers"
./scripts/kill_all.sh

echo "_____________________________________________ END"
