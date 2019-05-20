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

export BUILD_OPTIONS="--no-cache --force-rm --pull"

create_credentials
create_docker_assets
build_libraries_and_distribute

case "$1" in
    all)
        ./scripts/test_all.sh
    ;;

    core)
        ./scripts/test_container.sh kernel
        ./scripts/test_container.sh client
    ;;

    modules)
        ./scripts/test_container.sh odk
        ./scripts/test_container.sh couchdb-sync
    ;;

    integration)
        ./scripts/test_container.sh producer
        ./scripts/test_container.sh integration
    ;;

    *)
        # testing the given container
        ./scripts/test_container.sh $1
    ;;
esac
