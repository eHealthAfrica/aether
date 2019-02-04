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

# This script is a requisite for integration testing in Travis.
# To test locally, you likely have already done the things this script does.

AETHER_FUNCTIONS=scripts/aether_functions.sh

if [ ${1-} ]
then
    MODE="$1"
else
    MODE="default"
fi

if [ "$MODE" = "travis" ]
then
    ORDER=( "build_aether_utils_and_distribute" )
else
    ORDER=( "create_credentials"
            "create_aether_docker_assets"
            "create_version_files"
            "build_aether_utils_and_distribute"
            "build_common_and_distribute"
        )
fi

for FN in "${ORDER[@]}";
do
    $AETHER_FUNCTIONS $FN
done
