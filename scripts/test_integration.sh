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

# build_aether_containers.sh MUST be run before attempting integration tests.

function build_container() {
    echo "_____________________________________________ Building $1 container"
    $DC_TEST build "$1"-test
}

wait_for_kernel() {
    KERNEL_HEALTH_URL="http://localhost:9000/health"
    until curl -s $KERNEL_HEALTH_URL > /dev/null; do
        >&2 echo "Waiting for Kernel..."
        sleep 2
    done
}

if [ "$1" = "travis" ]
then
  echo "Using Travis testing configuration"
  DC_TEST="docker-compose -f docker-compose-travis-test.yml"
else
  DC_TEST="docker-compose -f docker-compose-test.yml"
fi

echo "_____________________________________________ TESTING"

$DC_TEST kill

echo "_____________________________________________ Starting database"
$DC_TEST up -d db-test

build_container kernel
echo "Building Travis pip cache..."
$DC_TEST run kernel-test travis_cache
run_container=$(docker ps -l -q)
docker commit $run_container aether-kernel:test
$DC_TEST run --no-deps kernel-test eval python /code/sql/create_readonly_user.py

until $DC_TEST run --no-deps kernel-test eval pg_isready -q; do
    >&2 echo "Waiting for db-test..."
    sleep 2
done

echo "_____________________________________________ Starting kernel"
$DC_TEST up -d kernel-test


echo "_____________________________________________ Starting Kafka"
$DC_TEST up -d zookeeper-test kafka-test

build_container producer
echo "_____________________________________________ Starting Producer"

$DC_TEST up -d producer-test

echo "_____________________________________________ Starting Integration Tests"
build_container integration
if [ "$1" = "travis" ]
then
  $DC_TEST run --no-deps integration-test travis_cache
  run_container=$(docker ps -l -q)
  docker commit $run_container aether-$1:test
fi
wait_for_kernel
$DC_TEST run --no-deps integration-test test

./scripts/kill_all.sh
echo "_____________________________________________ END"
