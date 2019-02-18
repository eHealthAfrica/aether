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

source ./scripts/aether_functions.sh

CONTAINERS=( kernel odk couchdb-sync ui producer integration-test )

# default values
build=no
containers=( kernel odk couchdb-sync ui producer )

while [[ $# -gt 0 ]]
do
    case "$1" in
        -b|--build)
            # build containers after upgrade
            build=yes

            shift # past argument
        ;;

        *)
            # otherwise is the container name
            containers=( "$1" )

            shift # past argument
        ;;
    esac
done

create_docker_assets
build_libraries_and_distribute

for container in "${CONTAINERS[@]}"
do
    pip_freeze_module $container

    if [[ $build = "yes" ]]
    then
        build_module $container
    fi
done

./scripts/kill_all.sh
