#!/bin/bash
set -e

DC_TEST="docker-compose -f docker-compose-common.yml"

# remove previous containers (clean start)
./scripts/kill_all.sh
$DC_TEST down

# test common module with different options

# Django 1.x compatibility
$DC_TEST build common-test-django-1
$DC_TEST run   common-test-django-1 test

# Django 2.x compatibility
$DC_TEST build common-test-django-2
$DC_TEST run   common-test-django-2 test

# create the distribution
$DC_TEST build common
$DC_TEST run   common build

PCK_FILE=aether.common-0.0.0-py2.py3-none-any.whl

# distribute within the containers
containers=( kernel odk-importer couchdb-sync )
for container in "${containers[@]}"
do
  cp -r ./aether-common/dist/$PCK_FILE ./aether-$container/conf/pip/dependencies/
done

./scripts/kill_all.sh
