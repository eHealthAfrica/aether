#!/usr/bin/env bash
set -e

function build_container() {
  echo "_________________________________________________ Building $1 container"
  $DC_TEST build "$1"-test
}

function kill_all(){
  echo "_________________________________________________ Killing Containers"
  $DC_TEST kill
  $DC_TEST down
}

DC_TEST="docker-compose -f aether-utils/aether-consumer/docker-compose.yml"

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

build_container consumer-sdk
$DC_TEST run consumer-sdk-test test

echo "_____________________________________________ Finished Test"

kill_all

echo "_____________________________________________ END"
