#!/bin/bash
set -e

DC_TEST="docker-compose -f docker-compose-test.yml"
$DC_TEST up -d db-test

# create the distribution
$DC_TEST run common-test build

PCK_FILE=aether.common-0.0.0-py2.py3-none-any.whl

# distribute within the containers
containers=( core odk-importer couchdb-sync ui )
for container in "${containers[@]}"
do
  cp -r ./aether-common/dist/$PCK_FILE ./aether-$container/conf/pip/dependencies/
done

$DC_TEST kill
