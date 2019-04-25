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

if [ ! -f VERSION ]; then
    APP_VERSION="0.0.0"
else
    APP_VERSION=`cat ./VERSION`
fi

# create the distribution
$DC_FILE build \
    --no-cache --force-rm --pull \
    --build-arg VERSION=$APP_VERSION \
    common
$DC_FILE run common
$DC_FILE down

# new release package name
PCK_FILE=aether.common-${APP_VERSION}-py2.py3-none-any.whl
# folder with all pip dependencies
PIP_DEPS=./local-setup/pip/dependencies/
# remove previous releases of the package
rm -f ${PIP_DEPS}/aether.common-*-py2.py3-none-any.whl
# copy new release
cp -r ./aether-common-library/dist/$PCK_FILE $PIP_DEPS

ls $PIP_DEPS

# distribute within the containers
FOLDERS=( aether-kernel aether-odk-module aether-couchdb-sync-module aether-ui )
for FOLDER in "${FOLDERS[@]}"
do
    DEST=./$FOLDER/conf/pip/
    # copy pip dependencies
    cp -r $PIP_DEPS $DEST

    echo "----------------------------------------------------------------------"
    echo "Distributed [${PCK_FILE}] into [$DEST]"
    echo "----------------------------------------------------------------------"
done
