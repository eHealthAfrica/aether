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
#   --build | -b  will build containers

#   <app>
#      Expected values: kernel, odk, couchdb-sync or sync.
#      Any other value will start all containers.
#

# default values
kill=no
build=no
container=all

while [[ $# -gt 0 ]]
do
    case "$1" in
        -f|--force)
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


# just show what's running
echo ""
docker-compose ps
echo ""


if [[ $kill = "yes" ]]
then
    echo "**********************************************************************"
    echo "**** Killing containers                                           ****"
    echo "**********************************************************************"

    ./scripts/kill_all.sh
fi


if [[ $build = "yes" ]]
then
    echo "**********************************************************************"
    echo "**** Building containers                                          ****"
    echo "**********************************************************************"

    ./scripts/build_aether_containers.sh
fi


echo "**********************************************************************"
echo "**** Starting PostgreSQL                                          ****"
echo "**********************************************************************"
docker-compose up -d db
until docker-compose run kernel eval pg_isready -q; do
    >&2 echo "Waiting for db..."
    sleep 2
done


CONTAINERS=( kernel ui odk couchdb-sync )
for app in "${CONTAINERS[@]}"
do
    docker-compose run $app setup
done

echo "**********************************************************************"
echo "**** Starting NGINX                                               ****"
echo "**********************************************************************"
docker-compose up -d --no-deps nginx


case $container in

    kernel)
        echo "**********************************************************************"
        echo "**** Starting Kernel app                                          ****"
        echo "**********************************************************************"

        docker-compose up kernel
    ;;

    odk)
        echo "**********************************************************************"
        echo "**** Starting Kernel app                                          ****"
        echo "**** Starting ODK module                                          ****"
        echo "**********************************************************************"

        docker-compose up kernel odk
    ;;

    sync|couchdb-sync)
        echo "**********************************************************************"
        echo "**** Starting CouchDB                                             ****"
        echo "**** Starting Redis                                               ****"
        echo "**** Starting RQ                                                  ****"
        echo "**********************************************************************"
        echo "**** Starting Kernel app                                          ****"
        echo "**** Starting CouchDB-Sync module                                 ****"
        echo "**********************************************************************"

        docker-compose up -d couchdb redis
        docker-compose up kernel couchdb-sync couchdb-sync-rq
    ;;

    ui)
        echo "**********************************************************************"
        echo "**** Starting Kernel app                                          ****"
        echo "**** Starting UI module                                           ****"
        echo "**** Starting UI assets HMR                                       ****"
        echo "**********************************************************************"

        docker-compose up db kernel ui ui-assets nginx
    ;;

    *)
        echo "**********************************************************************"
        echo "**** Starting CouchDB                                             ****"
        echo "**** Starting Redis                                               ****"
        echo "**** Starting RQ                                                  ****"
        echo "**********************************************************************"
        echo "**** Starting Kernel app                                          ****"
        echo "**** Starting ODK module                                          ****"
        echo "**** Starting CouchDB-Sync module                                 ****"
        echo "**********************************************************************"

        docker-compose up
    ;;

esac
