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

./scripts/build_common_and_distribute.sh

case "$1" in
    kubernetes)
        ./scripts/kubernetes/run_travis.sh
    ;;

    integration)
        ./scripts/test_integration_requires.sh travis
        ./scripts/test_integration.sh travis
    ;;

    all)
        ./scripts/test_all.sh travis
    ;;

    core)
        ./scripts/test_container.sh kernel travis
        ./scripts/test_container.sh client travis
    ;;

    modules)
        ./scripts/test_container.sh odk travis
        ./scripts/test_container.sh couchdb-sync travis
    ;;

    ui)
        ./scripts/test_container.sh ui travis
    ;;
    
    *)
        # testing the given container
        ./scripts/test_container.sh $1 travis
    ;;
esac
