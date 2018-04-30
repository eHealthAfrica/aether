#!/bin/bash
#
# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on anx
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
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
containers=( producer test-aether-integration )
for container in "${containers[@]}"
do
  if [[ $container = "producer" ]]
  then
    FOLDER=aether-$container
  else
    FOLDER=$container-module
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
    FOLDER=$container-module
  fi
  cp -r ./aether-utils/aether-mock-data/dist/$PCK_FILE ./$FOLDER/conf/pip/dependencies/
done

# create the saladbar distribution
$DC_CLIENT build saladbar
$DC_CLIENT run saladbar build

PCK_FILE=aether.saladbar-0.0.0-py2.py3-none-any.whl

# distribute within the containers
containers=( test-aether-integration )
for container in "${containers[@]}"
do
  if [[ $container = "producer" ]]
  then
    FOLDER=aether-$container
  else
    FOLDER=$container-module
  fi
  cp -r ./aether-utils/aether-saladbar/dist/$PCK_FILE ./$FOLDER/conf/pip/dependencies/
done


./scripts/kill_all.sh
