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

DC="docker-compose -f docker-compose-test.yml logs -t --tail=all"

case "$1" in
    core)
        $DC db-test
        echo "_____________________________________________"

        $DC kernel-test
        echo "_____________________________________________"
        $DC client-test
        echo "_____________________________________________"
    ;;

    modules)
        $DC db-test
        echo "_____________________________________________"
        $DC couchdb-test
        echo "_____________________________________________"
        $DC redis-test
        echo "_____________________________________________"

        $DC kernel-test
        echo "_____________________________________________"
        $DC odk-test
        echo "_____________________________________________"
        $DC couchdb-sync-test
        echo "_____________________________________________"
    ;;

    integration)
        $DC db-test
        echo "_____________________________________________"

        $DC kafka-test
        echo "_____________________________________________"
        $DC zookeeper-test
        echo "_____________________________________________"

        $DC kernel-test
        echo "_____________________________________________"
        $DC producer-test
        echo "_____________________________________________"
        $DC integration-test
        echo "_____________________________________________"
    ;;

    ui)
        $DC db-test
        echo "_____________________________________________"

        $DC kernel-test
        echo "_____________________________________________"
        $DC ui-test
        echo "_____________________________________________"
    ;;

    *)
        $DC
    ;;
esac
