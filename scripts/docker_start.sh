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
#   ./scripts/docker_start.sh [--force | --kill | -f | -k] [--build | -b] <name>
#
# arguments:
#   --force | -f   will kill all running containers
#   --kill  | -k   alias of the above
#   --build | -b   will kill and build containers before start

#   <name>
#      Expected values: kernel, odk, ui, couchdb-sync or sync.
#      Any other value will start all containers.
#

# default values
kill=no
build=no
app=

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
            app="$1"

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
echo "---- Starting containers                                          ----"
echo "----------------------------------------------------------------------"

# check given container name
case $app in
    kernel)
        CONTAINERS=(db kernel nginx)
    ;;
    odk)
        CONTAINERS=(db kernel odk nginx)
    ;;
    ui)
        CONTAINERS=(db kernel ui-assets ui nginx)
    ;;
    sync|couchdb-sync)
        app=couchdb-sync
        CONTAINERS=(db couchdb redis kernel couchdb-sync couchdb-sync-rq nginx)
    ;;
    *)
        app=
        CONTAINERS=(db couchdb redis kernel odk ui-assets ui couchdb-sync couchdb-sync-rq nginx)
    ;;
esac

for container in "${CONTAINERS[@]}"
do
    docker-compose up -d $container
    docker-compose logs --tail 20 $container
done

echo ""
docker-compose ps
echo "----------------------------------------------------------------------"
echo ""
docker ps
echo "----------------------------------------------------------------------"
echo ""

docker-compose logs -f $app
