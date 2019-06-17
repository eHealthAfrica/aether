#!/usr/bin/env bash
#
# Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
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

function show_help {
    echo """
    Upgrade python dependencies for the indicated services

    Usage:

        ./scripts/upgrade_container.sh [options] <name>

    Options:

        --build  | -b   build container with the new dependencies

        --help   | -h   show this message

        <name>
            Expected values: kernel, odk, ui, couchdb-sync or producer.
            In no name indicated then all the containers will be upgraded.
    """
}

# default values
build=no
containers=( kernel odk couchdb-sync ui producer )

while [[ $# -gt 0 ]]
do
    case "$1" in
        -h|--help)
            # shows help
            show_help
            exit 0
        ;;

        -b | --build )
            # build containers after upgrade
            build=yes

            shift # past argument
        ;;

        * )
            # otherwise is the container name
            containers=( "$1" )

            shift # past argument
        ;;
    esac
done

create_docker_assets

for container in "${containers[@]}"
do
    pip_freeze_container $container

    if [[ $build = "yes" ]]
    then
        build_container $container
    fi
done

./scripts/kill_all.sh
