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

function show_help {
    echo """
    Start the indicated container with the necessary dependencies

    Usage:

        ./scripts/docker_start.sh [options] <name>

    Options:

        --build | -b   kill and build all containers before start
        --clean | -c   stop and remove all running containers and volumes before start
        --force | -f   ensure that the container will be restarted if needed
        --kill  | -k   kill all running containers before start

        --help  | -h   show this message

        <name>
            Expected values: kernel, odk, ui, couchdb-sync or sync (alias of couchdb-sync).
            Any other value will start all containers.

    """
}

function start_container {
    if [[ $force = "yes" ]]; then
        docker-compose kill $1
    fi
    docker-compose up --no-deps -d $1
    sleep 2
    docker-compose logs --tail 20 $1
}

# default values
app=
build=no
clean=no
force=no
kill=no

while [[ $# -gt 0 ]]
do
    case "$1" in
        -h|--help)
            # shows help
            show_help
            exit 0
        ;;

        -k|--kill)
            # stop all containers
            kill=yes

            shift # past argument
        ;;

        -b|--build)
            # build all containers
            build=yes

            shift # past argument
        ;;

        -c|--clean)
            # clean all containers
            kill=yes
            clean=yes

            shift # past argument
        ;;

        -f|--force)
            # force restart container
            force=yes

            shift # past argument
        ;;

        *)
            # otherwise is the container name
            app="$1"

            shift # past argument
        ;;
    esac
done

case $app in
    kernel)
        PRE_CONTAINERS=(db nginx minio keycloak)
        SETUP_CONTAINERS=(kernel)
        POST_CONTAINERS=()
    ;;

    odk)
        PRE_CONTAINERS=(db nginx minio keycloak)
        SETUP_CONTAINERS=(kernel odk)
        POST_CONTAINERS=()
    ;;

    ui)
        PRE_CONTAINERS=(ui-assets db nginx minio keycloak)
        SETUP_CONTAINERS=(kernel ui)
        POST_CONTAINERS=(ui)
    ;;

    sync|couchdb-sync)
        app=couchdb-sync

        PRE_CONTAINERS=(db couchdb redis nginx minio keycloak)
        SETUP_CONTAINERS=(kernel couchdb-sync)
        POST_CONTAINERS=(couchdb-sync-rq)
    ;;

    *)
        app=

        PRE_CONTAINERS=(ui-assets db couchdb redis nginx minio keycloak)
        SETUP_CONTAINERS=(kernel odk ui couchdb-sync)
        POST_CONTAINERS=(couchdb-sync-rq)
    ;;
esac

create_credentials

echo ""
docker-compose ps
echo "----------------------------------------------------------------------"
echo ""

if [[ $kill = "yes" ]]
then
    echo "----------------------------------------------------------------------"
    echo "---- Killing containers                                           ----"
    echo "----------------------------------------------------------------------"

    ./scripts/kill_all.sh
    echo ""
fi

if [[ $clean = "yes" ]]
then
    echo "----------------------------------------------------------------------"
    echo "---- Cleaning containers and volumes                              ----"
    echo "----------------------------------------------------------------------"

    ./scripts/clean_all.sh
    echo ""
fi

create_docker_assets

if [[ $build = "yes" ]]
then
    echo "----------------------------------------------------------------------"
    echo "---- Building containers                                          ----"
    echo "----------------------------------------------------------------------"

    build_libraries_and_distribute
    build_ui_assets

    for container in "${SETUP_CONTAINERS[@]}"
    do
        build_container $container
    done
    echo ""
fi

echo "----------------------------------------------------------------------"
echo "---- Starting containers                                          ----"
echo "----------------------------------------------------------------------"

for container in "${PRE_CONTAINERS[@]}"
do
    start_container $container
done

for container in "${SETUP_CONTAINERS[@]}"
do
    docker-compose run $container setup
    start_container $container
done

for container in "${POST_CONTAINERS[@]}"
do
    start_container $container
done

echo ""
docker-compose ps
echo "----------------------------------------------------------------------"
echo ""
docker ps
echo "----------------------------------------------------------------------"
echo ""

docker-compose up $app
