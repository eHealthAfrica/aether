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

source ./scripts/_lib.sh

create_credentials
create_docker_assets

if [[ $1 == "ui" ]]; then
    build_ui_assets
fi

if [[ $1 == "integration" ]]; then
    build_client
fi

build_container $1

if [[ $1 == "kernel" ]]; then
    create_readonly_user
fi

./scripts/clean_all.sh
