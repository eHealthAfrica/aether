#!/usr/bin/env bash
set -e

function prepare_container() {
  echo "_________________________________________________ Preparing $1 container"
  $DC_TEST build "$1"-test
  $DC_TEST run "$1"-test setuplocaldb
  echo "_________________________________________________ $1 ready!"
}


if [ -n "$1" ];
then
  # take container name from argument, expected values `odk` or `couchdb-sync`
  echo "Executing tests for $1 container"
  container=$1
else
  echo "Nothing to do."
  exit 0
fi

DC_TEST="docker-compose -f docker-compose-test.yml"

# make sure that there is nothing up before starting
echo "_____________________________________________ Killing ALL containers"
./scripts/kill_all.sh
$DC_TEST down

# start databases
echo "_____________________________________________ Starting databases"

if [[ $container = "odk" ]]
then
  $DC_TEST up -d db-test
  fixture=aether/kernel/api/tests/fixtures/project_empty_schema.json
else
  $DC_TEST up -d db-test couchdb-test redis-test
  fixture=aether/kernel/api/tests/fixtures/project.json
fi

# prepare and start KERNEL container
prepare_container kernel

echo "_____________________________________________ Starting kernel"
$DC_TEST up -d kernel-test
if [[ $container != "client" ]]
then
  $DC_TEST run kernel-test manage loaddata $fixture
fi
echo "_____________________________________________ Loaded initial data in kernel"

# build test container
prepare_container $container

# run tests
echo "_____________________________________________ Testing $container"
$DC_TEST run "$container"-test test

# kill auxiliary containers
echo "_____________________________________________ Killing auxiliary containers"
./scripts/kill_all.sh

echo "_____________________________________________ END"
