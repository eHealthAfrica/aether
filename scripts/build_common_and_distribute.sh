#!/usr/bin/env bash
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

DC_FILE="docker-compose -f ./aether-common-library/docker-compose.yml"
$DC_FILE down

APP_REVISION=`git rev-parse --abbrev-ref HEAD`
APP_VERSION=`cat ./VERSION`

# create the distribution
$DC_FILE build \
    --no-cache --force-rm --pull \
    --build-arg GIT_REVISION=$APP_REVISION \
    --build-arg VERSION=$APP_VERSION \
    common
$DC_FILE run common build

PCK_FILE=aether.common-${APP_VERSION}-py2.py3-none-any.whl

# distribute within the containers
FOLDERS=( aether-kernel aether-odk-module aether-couchdb-sync-module aether-ui )
for FOLDER in "${FOLDERS[@]}"
do
    DEST=./$FOLDER/conf/pip/dependencies/
    mkdir -p $DEST
    cp -r ./aether-common-library/dist/$PCK_FILE $DEST

    echo "----------------------------------------------------------------------"
    echo "Distributed [${PCK_FILE}] into [$DEST]"
    echo "----------------------------------------------------------------------"
done

$DC_FILE kill
