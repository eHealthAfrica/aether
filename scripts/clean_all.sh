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

source .env

function show_help {
    echo """
    Remove containers for services defined in all the compose files

    Usage:

        ./scripts/clean_all.sh [options]

    Options:

        --env-file | -e   remove also the [.env] file (contains all credentials)
        --network  | -n   remove also the network: ${NETWORK_NAME}
        --volume   | -v   remove also the volume: ${DB_VOLUME}
        --all      | -a   remove all of the above

        --help     | -h   show this message
    """
}

# default values
network=no
volume=no
env=no

while [[ $# -gt 0 ]]
do
    case "$1" in
        -h|--help)
            # shows help
            show_help
            exit 0
        ;;

        -e|--env-file)
            # remove credentials
            env=yes
            shift # past argument
        ;;

        -v|--volume)
            # remove volume
            volume=yes
            shift # past argument
        ;;

        -n|--network)
            # remove network
            network=yes
            shift # past argument
        ;;

        -a|--all)
            # remove volume, network and credentials
            volume=yes
            network=yes
            env=yes
            shift # past argument
        ;;

        *)
            shift # past argument
        ;;
    esac
done

# libraries
docker-compose -f ./aether-client-library/docker-compose.yml kill
docker-compose -f ./aether-client-library/docker-compose.yml down

docker-compose -f ./aether-common-library/docker-compose.yml kill
docker-compose -f ./aether-common-library/docker-compose.yml down

# core apps
for dc_file in $(find docker-compose*.yml 2> /dev/null)
do
    docker-compose -f $dc_file kill
    docker-compose -f $dc_file down
done

if [[ $volume = "yes" ]]; then
    docker volume  rm ${DB_VOLUME}
fi

if [[ $network = "yes" ]]; then
    docker network rm ${NETWORK_NAME}
fi

if [[ $env = "yes" ]]; then
    rm -f .env
fi
