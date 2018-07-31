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

DC_TEST="docker-compose -f docker-compose-test.yml"
$DC_TEST kill
$DC_TEST down

echo "_____________________________________________ TESTING"

echo "_____________________________________________ Starting database"
$DC_TEST up -d db-test


echo "_____________________________________________ Building kernel container"
$DC_TEST build kernel-test
echo "_____________________________________________ kernel ready!"
$DC_TEST run   kernel-test test
echo "_____________________________________________ kernel tests passed"


containers=( odk couchdb-sync ui )

for container in "${containers[@]}"
do :
    ./scripts/test_with_kernel.sh $container
done


echo "_____________________________________________ END"
