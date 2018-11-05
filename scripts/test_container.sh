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

wait_for_kernel() {
    KERNEL_HEALTH_URL="http://localhost:9000/health"
    until curl -s $KERNEL_HEALTH_URL > /dev/null; do
        >&2 echo "Waiting for Kernel..."
        sleep 2
    done
}

if [ "$#" -ne 2 ]
then
  DC_TEST="docker-compose -f docker-compose-test.yml"
else
  echo "Using Travis testing configuration"
  DC_TEST="docker-compose -f docker-compose-travis-test.yml"
fi


./scripts/kill_all.sh
$DC_TEST down

if [[ $1 == "ui" ]]
then
    $DC_TEST build ui-assets-test
    $DC_TEST run   ui-assets-test test
    $DC_TEST run   ui-assets-test build
    echo "_____________________________________________ Tested and built ui assets"
fi


echo "_____________________________________________ Starting databases"
$DC_TEST up -d db-test
if [[ $1 = "couchdb-sync" ]]
then
    $DC_TEST up -d couchdb-test redis-test
fi

# sometimes this is not as faster as we wanted... :'(
$DC_TEST build kernel-test
until $DC_TEST run kernel-test eval pg_isready -q; do
    >&2 echo "Waiting for db-test..."
    sleep 2
done


if [[ $1 != "kernel" ]]
then
    echo "_____________________________________________ Starting kernel"
    # rename kernel test database in each case
    export TEST_KERNEL_DB_NAME=test-kernel-"$1"
    $DC_TEST up -d kernel-test
fi


echo "_____________________________________________ Preparing $1 container"
$DC_TEST build "$1"-test
echo "_____________________________________________ $1 ready!"


if [ "$2" = "travis" ]
then
    $DC_TEST run "$1"-test travis_cache
fi
if [[ $1 != "kernel" ]]
then
    wait_for_kernel
fi
$DC_TEST run "$1"-test test

echo "_____________________________________________ $1 tests passed!"


./scripts/kill_all.sh
