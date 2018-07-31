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

if [ -n "$1" ];
then
    # expected values: `odk`, `couchdb-sync`, `ui`, `client`
    echo "Executing tests for $1 container"
else
    echo "Nothing to do."
    exit 0
fi

DC_TEST="docker-compose -f docker-compose-test.yml"
$DC_TEST kill
$DC_TEST down

echo "_____________________________________________ TESTING $1 container"

echo "_____________________________________________ Starting database"
$DC_TEST up -d db-test

echo "_____________________________________________ Starting kernel"
$DC_TEST up --build -d kernel-test

if [[ $1 == "couchdb-sync" ]]
then
    fixture=aether/kernel/api/tests/fixtures/project.json
    $DC_TEST run kernel-test manage loaddata $fixture
    echo "_____________________________________________ Loaded initial data in kernel"

    echo "_____________________________________________ Starting auxiliary databases"
    $DC_TEST up -d couchdb-test redis-test
fi

if [[ $1 == "ui" ]]
then
    $DC_TEST build ui-assets-test
    $DC_TEST run   ui-assets-test test
    $DC_TEST run   ui-assets-test build
    echo "_____________________________________________ Tested and built assets"
fi

echo "_____________________________________________ Preparing $1 container"
$DC_TEST build "$1"-test
echo "_____________________________________________ $1 ready!"
$DC_TEST run "$1"-test test
echo "_____________________________________________ $1 tests passed!"


echo "_____________________________________________ Killing TEST containers"
$DC_TEST kill

echo "_____________________________________________ END"
