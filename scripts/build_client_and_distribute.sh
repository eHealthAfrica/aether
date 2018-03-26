#!/bin/bash
set -e

DC_CLIENT="docker-compose -f docker-compose-build-aether-utils.yml"

# remove previous containers (clean start)
./scripts/kill_all.sh
$DC_CLIENT down

# create the client distribution
$DC_CLIENT build client
$DC_CLIENT run client build

PCK_FILE=aether.client-0.0.0-py2.py3-none-any.whl

# distribute within the containers
containers=( producer, test-aether-integration )
for container in "${containers[@]}"
do
  if [[ $container = "producer" ]]
  then
    FOLDER=aether-$container
  else
    FOLDER=aether-$container-module
  fi
  cp -r ./aether-utils/aether-client/dist/$PCK_FILE ./$FOLDER/conf/pip/dependencies/
done

# create the mocker distribution
$DC_CLIENT build mocker
$DC_CLIENT run mocker build

PCK_FILE=aether.mocker-0.0.0-py2.py3-none-any.whl

# distribute within the containers
containers=( test-aether-integration )
for container in "${containers[@]}"
do
  if [[ $container = "producer" ]]
  then
    FOLDER=aether-$container
  else
    FOLDER=aether-$container-module
  fi
  cp -r ./aether-utils/aether-mock-data/dist/$PCK_FILE ./$FOLDER/conf/pip/dependencies/
done

# create the saladbar distribution
$DC_CLIENT build saladbar
$DC_CLIENT run saladbar build

PCK_FILE=saladbar-0.0.0-py2.py3-none-any.whl

# distribute within the containers
containers=( test-aether-integration )
for container in "${containers[@]}"
do
  if [[ $container = "producer" ]]
  then
    FOLDER=aether-$container
  else
    FOLDER=aether-$container-module
  fi
  cp -r ./aether-utils/aether-saladbar/dist/$PCK_FILE ./$FOLDER/conf/pip/dependencies/
done


./scripts/kill_all.sh
