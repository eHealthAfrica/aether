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

DC_UTILS="docker-compose -f docker-compose-build-aether-utils.yml"

# remove previous containers (clean start)
./scripts/kill_all.sh
$DC_UTILS down

# create the distribution
$DC_UTILS build common
$DC_UTILS run   common build

PCK_FILE=aether.common-0.0.0-py2.py3-none-any.whl

# distribute within the containers
FOLDERS=( aether-kernel aether-odk-module aether-couchdb-sync-module aether-ui )
for FOLDER in "${FOLDERS[@]}"
do
    mkdir -p ./$FOLDER/conf/pip/dependencies
    cp -r ./aether-common-module/dist/$PCK_FILE ./$FOLDER/conf/pip/dependencies/
done

./scripts/kill_all.sh
