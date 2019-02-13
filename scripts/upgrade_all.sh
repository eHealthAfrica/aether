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

# create the common module
./scripts/build_common_and_distribute.sh

# default values
build=no
containers=( kernel odk couchdb-sync ui )

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


for container in "${containers[@]}"
do
    # upgrade pip dependencies
    echo "_____________________________________________ Updating $container"
    docker-compose run --no-deps $container pip_freeze
    echo "_____________________________________________ $container updated!"

    if [[ $build = "yes" ]]
    then
        echo "_____________________________________________ Rebuilding $container with updates"
        docker-compose build --no-cache $container
        echo "_____________________________________________ $container rebuilt!"
    fi
done


# special case
echo "_____________________________________________ Updating producer"
docker-compose -f docker-compose-connect.yml run --no-deps producer pip_freeze
echo "_____________________________________________ producer updated!"

./scripts/kill_all.sh
