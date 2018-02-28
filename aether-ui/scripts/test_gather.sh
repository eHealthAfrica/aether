#!/usr/bin/env bash
set -e

function prepare_container() {
  container="$1"-test

  echo "_____________________________________________ Preparing $1"
  $DC_TEST build $container
  $DC_TEST run $container setuplocaldb
}

function prepare_and_test_container() {
  container="$1"-test

  echo "_____________________________________________ Starting $1 tasks"
  prepare_container $1
  $DC_TEST run $container test --noinput
  echo "_____________________________________________ $1 tasks done"
}

function prepare_and_test_gather_test_container () {
    echo "_____________________________________________ Starting gather-test tasks"
    $DC_TEST build gather-test
    $DC_TEST run gather-test setuptestdb
    $DC_TEST run gather-test test --noinput
    echo "_____________________________________________ gather-test tasks done"
}

DC_TEST="docker-compose -f docker-compose-test.yml"

echo "_____________________________________________ TESTING"

# kill ALL containers and clean TEST ones
echo "_____________________________________________ Killing ALL containers"
docker-compose kill
$DC_TEST kill
$DC_TEST down

# start database
echo "_____________________________________________ Starting databases"
$DC_TEST up -d db-test

# prepare kernel with initial project
echo "_____________________________________________ Preparing kernel and odk"
prepare_container kernel
prepare_container odk

echo "_____________________________________________ Starting kernel and odk"
$DC_TEST up -d kernel-test odk-test

# test a clean Gather TEST container
prepare_and_test_gather_test_container

# kill ALL containers
echo "_____________________________________________ Killing auxiliary containers"
$DC_TEST kill

echo "_____________________________________________ END"
