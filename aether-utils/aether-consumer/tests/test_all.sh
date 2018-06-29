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
set -Eeuo pipefail

function build_container() {
  echo "_________________________________________________ Building $1 container"
  $DC_TEST build "$1"-test
}

function kill_all(){
  echo "_________________________________________________ Killing Containers"
  $DC_TEST kill
  $DC_TEST down
}

DC_TEST="docker-compose -f ../docker-compose.yml"

echo "_____________________________________________ TESTING"
kill_all
build_container kafka
build_container zookeeper
echo "_____________________________________________ Starting Kafka"
$DC_TEST up -d zookeeper-test kafka-test

# test a clean INGEGRATION TEST container
echo "_____________________________________________ Starting Python2 Tests"

build_container consumer-sdk-py2
$DC_TEST run consumer-sdk-py2-test test

echo "_____________________________________________ Finished Test"


kill_all
build_container kafka
build_container zookeeper
echo "_____________________________________________ Starting Kafka"
$DC_TEST up -d zookeeper-test kafka-test

echo "_____________________________________________ Starting Python3 Tests"

build_container consumer-sdk-py3
$DC_TEST run consumer-sdk-py3-test test

echo "_____________________________________________ Finished Test"

kill_all

echo "_____________________________________________ END"
