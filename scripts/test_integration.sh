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
$DC_TEST down

./scripts/build_aether_utils_and_distribute.sh

echo "_____________________________________________ TESTING"

echo "_____________________________________________ Starting Database"
$DC_TEST up -d db-test

echo "_____________________________________________ Starting Kernel"
$DC_TEST up --build -d kernel-test

echo "_____________________________________________ Testing Client"
$DC_TEST build client-test
$DC_TEST run   client-test test

echo "_____________________________________________ Starting Kafka"
$DC_TEST up -d zookeeper-test kafka-test

echo "_____________________________________________ Starting Producer"
$DC_TEST up --build -d producer-test

echo "_____________________________________________ Starting Integration Tests"
$DC_TEST build integration-test
$DC_TEST run   integration-test test

echo "_____________________________________________ Killing TEST containers"
$DC_TEST kill

echo "_____________________________________________ END"
