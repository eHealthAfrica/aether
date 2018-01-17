#!/bin/bash
set -e

DC_COMMON="docker-compose -f docker-compose-common.yml"

# remove previous containers (clean start)
./scripts/kill_all.sh
$DC_COMMON down

# test common module with different options

# Django 1.x compatibility
$DC_COMMON build common-test-django-1
$DC_COMMON run   common-test-django-1 test

# Django 2.x compatibility
$DC_COMMON build common-test-django-2
$DC_COMMON run   common-test-django-2 test

# create the distribution
$DC_COMMON build common
$DC_COMMON run   common build

PCK_FILE=aether.common-0.0.0-py2.py3-none-any.whl

# distribute within the containers
containers=( kernel odk couchdb-sync )
for container in "${containers[@]}"
do
  if [[ $container = "kernel" ]]
  then
    FOLDER=aether-$container
  else
    FOLDER=aether-$container-module
  fi
  cp -r ./aether-common-module/dist/$PCK_FILE ./$FOLDER/conf/pip/dependencies/
done

./scripts/kill_all.sh
