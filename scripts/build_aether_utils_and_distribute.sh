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

DC_UTILS="docker-compose -f ./aether-utils/docker-compose.yml"

$DC_UTILS down

UTILS=( client mocker )
for UTIL in "${UTILS[@]}"
do

    # create the distribution
    $DC_UTILS build $UTIL
    $DC_UTILS run $UTIL build
    PCK_FILE=aether.$UTIL-0.0.0-py2.py3-none-any.whl

    if [[ $UTIL = "mocker" ]]
    then
        SRC=mock-data
    else
        SRC=$UTIL
    fi

    if [[ $UTIL = "client" ]]
    then
        FOLDERS=( test-aether-integration-module aether-producer )
    else
        FOLDERS=( test-aether-integration-module )
    fi

    # distribute within the containers
    for FOLDER in "${FOLDERS[@]}"
    do
        FILE=./aether-utils/aether-$SRC/dist/$PCK_FILE
        DEST=./$FOLDER/conf/pip/dependencies/

        mkdir -p $DEST
        cp -r $FILE $DEST

        echo "----------------------------------------------------------------------"
        echo "Distributed [$FILE] into [$DEST]"
        echo "----------------------------------------------------------------------"
    done

done

$DC_UTILS kill
