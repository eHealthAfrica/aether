#!/usr/bin/env bash
set -e

function prepare_and_test_container() {
  container="$1"-test

  echo "_____________________________________________ Starting $1 tasks"
  $DC_TEST build $container
  $DC_TEST run $container setuplocaldb
  if [[ $2 ]]
  then
    docker-compose -f docker-compose-test.yml run kernel-test manage loaddata $2
  fi
  $DC_TEST run $container test --noinput
  echo "_____________________________________________ $1 tasks done"
}

DC_TEST="docker-compose -f docker-compose-test.yml"

echo "_____________________________________________ TESTING"

# kill ALL containers and clean TEST ones
echo "_____________________________________________ Killing ALL containers"
docker-compose kill
$DC_TEST kill
$DC_TEST down

# start databases
echo "_____________________________________________ Starting databases"
$DC_TEST up -d db-test couchdb-test redis-test

# test and start a clean KERNEL TEST container
prepare_and_test_container kernel

echo "_____________________________________________ Starting kernel"
$DC_TEST up -d kernel-test

# test and start a clean ODK TEST container
prepare_and_test_container odk-importer aether/kernel/api/tests/fixtures/project_empty_schema.json

echo "_____________________________________________ Starting odk-importer"
$DC_TEST up -d odk-importer-test

# test a clean SYNC TEST container
prepare_and_test_container couchdb-sync aether/kernel/api/tests/fixtures/project.json

# FIXME: run ui tests
# # test a clean UI TEST container
# prepare_and_test_container ui

# kill ALL containers
echo "_____________________________________________ Killing auxiliary containers"
$DC_TEST kill

echo "_____________________________________________ END"
