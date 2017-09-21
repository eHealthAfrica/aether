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
  # take container name from argument, expected values `odk-importer` or `couchdb-sync`
  echo "Executing tests for $1 container"
  container=$1
else
  echo "Nothing to do."
  exit 0
fi

DC_TEST="docker-compose -f docker-compose-test.yml"

# make sure that there is nothing up before starting
echo "_____________________________________________ Killing ALL containers"
docker-compose kill
$DC_TEST kill
$DC_TEST down

# start databases
echo "_____________________________________________ Starting databases"
$DC_TEST up -d db-test couchdb-test redis-test

# prepare and start CORE container
prepare_container core

echo "_____________________________________________ Starting core"
$DC_TEST up -d core-test

# build test container
prepare_container $container

# run tests
echo "_____________________________________________ Testing $container"
$DC_TEST run "$container"-test test

# kill auxiliary containers
echo "_____________________________________________ Killing auxiliary containers"
$DC_TEST kill

echo "_____________________________________________ END"
