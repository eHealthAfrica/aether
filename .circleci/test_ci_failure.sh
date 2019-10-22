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

DC="docker-compose -f docker-compose-test.yml logs -t --tail=all"
LINE=`printf -v row "%${COLUMNS:-$(tput cols)}s"; echo ${row// /+}`

case "$1" in
    core)
        $DC db-test
        echo "${LINE}"

        $DC kernel-test
        echo "${LINE}"
        $DC client-test
        echo "${LINE}"
    ;;

    modules)
        $DC db-test
        echo "${LINE}"
        $DC couchdb-test
        echo "${LINE}"
        $DC redis-test
        echo "${LINE}"

        $DC kernel-test
        echo "${LINE}"
        $DC odk-test
        echo "${LINE}"
        $DC couchdb-sync-test
        echo "${LINE}"
    ;;

    integration)
        $DC db-test
        echo "${LINE}"

        $DC kafka-test
        echo "${LINE}"
        $DC zookeeper-test
        echo "${LINE}"

        $DC kernel-test
        echo "${LINE}"
        $DC producer-test
        echo "${LINE}"
        $DC integration-test
        echo "${LINE}"
    ;;

    ui)
        $DC db-test
        echo "${LINE}"

        $DC kernel-test
        echo "${LINE}"
        $DC ui-test
        echo "${LINE}"
    ;;

    *)
        $DC
    ;;
esac
