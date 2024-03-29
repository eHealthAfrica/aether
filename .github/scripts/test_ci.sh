#!/usr/bin/env bash
#
# Copyright (C) 2023 by eHealth Africa : http://www.eHealthAfrica.org
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

source ./scripts/_lib.sh

create_credentials
create_docker_assets

case "$1" in
    all)
        ./scripts/test_all.sh
    ;;

    core)
        ./scripts/test_container.sh kernel
        ./scripts/test_container.sh exm
        ./scripts/test_container.sh producer
    ;;

    modules)
        ./scripts/test_container.sh odk
    ;;

    integration)
        ./scripts/test_container.sh client

        build_client

        # check producer access to kernel via REST API
        export KERNEL_ACCESS_TYPE=api
        ./scripts/test_container.sh integration

        # check producer access to kernel via database
        export KERNEL_ACCESS_TYPE=db
        ./scripts/test_container.sh integration
    ;;

    *)
        # testing the given container
        ./scripts/test_container.sh $1
    ;;
esac
