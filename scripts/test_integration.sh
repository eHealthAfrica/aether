#!/usr/bin/env bash
set -e

function prepare_and_test_container() {
  container="$1"-test

  echo "_____________________________________________ Starting $1 tasks"
  $DC_TEST build $container
  $DC_TEST run   $container setuplocaldb
  if [[ $2 ]]
  then
    $DC_TEST run kernel-test manage loaddata $2
  fi
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

# start databases
echo "_____________________________________________ Starting database"
$DC_TEST up -d db-test

# start a clean KERNEL TEST container
prepare_container kernel

echo "_____________________________________________ Starting kernel"
$DC_TEST up -d kernel-test

build_container kafka
build_container zookeeper
echo "_____________________________________________ Starting Kafka"
$DC_TEST up -d zookeeper-test kafka-test

build_container producer
echo "_____________________________________________ Starting Producer"
$DC_TEST up -d producer-test

# test a clean INGEGRATION TEST container
echo "_____________________________________________ Starting Integration Tests"
build_container integration
$DC_TEST run integration-test test

# kill ALL containers
echo "_____________________________________________ Killing auxiliary containers"
./scripts/kill_all.sh

echo "_____________________________________________ END"
