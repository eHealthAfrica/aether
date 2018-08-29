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

# start the indicated app/module with the necessary dependencies
#
#   docker_start.sh [--force | -f] [--build | -b] <app>
#
# arguments:
#   --force | -f  will kill running containers
#   --killl | -k  will kill running containers
#   --build | -b  will build containers

#   <app>
#      Expected values: kernel, odk, ui, couchdb-sync or sync.
#      Another value will start all containers.
#

# default values
kill=no
build=no
container=all

while [[ $# -gt 0 ]]
do
    case "$1" in
        -f|--force|-k|--kill)
            # stop all containers
            kill=yes

            shift # past argument
        ;;

        -b|--build)
            # build all containers
            build=yes

            shift # past argument
        ;;

        *)
            # otherwise is the container name
            container="$1"

            shift # past argument
        ;;
    esac
done


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


if [[ $build = "yes" ]]
then
    echo "----------------------------------------------------------------------"
    echo "---- Building containers                                          ----"
    echo "----------------------------------------------------------------------"

    ./scripts/build_aether_containers.sh
    echo ""
fi


echo "----------------------------------------------------------------------"
echo "---- Starting databases                                           ----"
echo "----------------------------------------------------------------------"
docker-compose up -d db
case $container in
    kernel|odk|ui)
        # nothing to do
    ;;
    *)
        docker-compose up -d couchdb
        docker-compose up -d redis
    ;;
esac
echo ""


echo "----------------------------------------------------------------------"
echo "---- Starting containers                                          ----"
echo "----------------------------------------------------------------------"

docker-compose up -d kernel

case $container in
    kernel)
        # nothing to do
    ;;

    odk)
        docker-compose up -d odk
    ;;

    sync|couchdb-sync)
        docker-compose up -d couchdb-sync
        docker-compose up -d couchdb-sync-rq
    ;;

    ui)
        docker-compose up -d ui-assets
        docker-compose up -d ui
    ;;

    *)
        docker-compose up -d odk

        docker-compose up -d couchdb-sync
        docker-compose up -d couchdb-sync-rq

        docker-compose up -d ui-assets
        docker-compose up -d ui
    ;;

esac
echo ""


echo "----------------------------------------------------------------------"
echo "---- Starting NGINX                                               ----"
echo "----------------------------------------------------------------------"
docker-compose kill nginx
docker-compose up -d nginx
echo ""

sleep 5

echo ""
docker-compose ps
echo "----------------------------------------------------------------------"
echo ""
docker ps
echo "----------------------------------------------------------------------"
echo ""
