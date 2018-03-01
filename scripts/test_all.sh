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
  $DC_TEST build "$1"-test
  $DC_TEST run "$1"-test setuplocaldb
  echo "_________________________________________________ $1 ready!"
}

DC_TEST="docker-compose -f docker-compose-test.yml"
DC_COMMON="docker-compose -f docker-compose-common.yml"

echo "_____________________________________________ TESTING"

# kill ALL containers and clean TEST ones
echo "_____________________________________________ Killing ALL containers"
./scripts/kill_all.sh
$DC_TEST down

echo "_____________________________________________ Testing common module"
$DC_COMMON down
$DC_COMMON build
$DC_COMMON run common test

# start databases
echo "_____________________________________________ Starting databases"
$DC_TEST up -d db-test couchdb-test redis-test

# test and start a clean KERNEL TEST container
prepare_and_test_container kernel

echo "_____________________________________________ Starting kernel"
$DC_TEST up -d kernel-test

# test a clean CLIENT TEST container
prepare_and_test_container client

# test and start a clean ODK TEST container
prepare_and_test_container odk aether/kernel/api/tests/fixtures/project_empty_schema.json

# test a clean SYNC TEST container
prepare_and_test_container couchdb-sync aether/kernel/api/tests/fixtures/project.json

prepare_and_test_container ui
# kill ALL containers
echo "_____________________________________________ Killing auxiliary containers"
./scripts/kill_all.sh

echo "_____________________________________________ END"
