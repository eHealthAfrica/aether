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

DC_TEST="docker-compose -f docker-compose-test.yml"

echo "_____________________________________________ TESTING"

# kill ALL containers and clean TEST ones
echo "_____________________________________________ Killing ALL containers"
./scripts/kill_all.sh
$DC_TEST down

# start databases
echo "_____________________________________________ Starting databases"
$DC_TEST up -d db-test couchdb-test redis-test

# test and start a clean KERNEL TEST container
prepare_and_test_container kernel

echo "_____________________________________________ Starting kernel"
$DC_TEST up -d kernel-test

# test and start a clean ODK TEST container
prepare_and_test_container odk aether/kernel/api/tests/fixtures/project_empty_schema.json

echo "_____________________________________________ Starting odk"
$DC_TEST up -d odk-test

# test a clean SYNC TEST container
prepare_and_test_container couchdb-sync aether/kernel/api/tests/fixtures/project.json

# kill ALL containers
echo "_____________________________________________ Killing auxiliary containers"
./scripts/kill_all.sh

echo "_____________________________________________ END"
