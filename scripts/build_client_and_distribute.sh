#!/bin/bash
set -e

DC_CLIENT="docker-compose -f docker-compose-client.yml"

# remove previous containers (clean start)
./scripts/kill_all.sh
$DC_CLIENT down

# create the distribution
$DC_CLIENT build client
$DC_CLIENT run client build

PCK_FILE=aether.client-0.0.0-py2.py3-none-any.whl

# distribute within the containers
containers=( producer )
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

./scripts/kill_all.sh
