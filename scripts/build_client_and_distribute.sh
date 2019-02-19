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
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
set -Eeuo pipefail

DC_FILE="docker-compose -f ./aether-client-library/docker-compose.yml"
$DC_FILE down

APP_VERSION=`cat ./VERSION`

# create the distribution
$DC_FILE build \
    --build-arg VERSION=$APP_VERSION \
    client
$DC_FILE run client build

PCK_FILE=aether.client-${APP_VERSION}-py2.py3-none-any.whl

# distribute within the containers
FOLDERS=( test-aether-integration-module aether-producer )
for FOLDER in "${FOLDERS[@]}"
do
    DEST=./${FOLDER}/conf/pip/dependencies/
    mkdir -p ${DEST}

    cp -r ./aether-client-library/dist/${PCK_FILE} ${DEST}

    echo "----------------------------------------------------------------------"
    echo "Distributed [${PCK_FILE}] into [$DEST]"
    echo "----------------------------------------------------------------------"
done

$DC_FILE kill
