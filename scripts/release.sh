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

set -Eo pipefail

source scripts/release_lib.sh


TAG_INCREASED_VERSION="0.0.0"
VERSION=
if [ ! -f VERSION ]; then
    FILE_VERSION=$TAG_INCREASED_VERSION
else
    FILE_VERSION=`cat VERSION`
    VERSION=$FILE_VERSION
fi


# release version depending on TRAVIS_BRANCH (develop | release-#.#) / TRAVIS_TAG (#.#.#)
if [[ ${TRAVIS_TAG} =~ ^[0-9]+(\.[0-9]+){2}$ ]]; then

    VERSION=$TRAVIS_TAG
    # Release with unified branch and file versions
    git_branch_commit_and_release ${FILE_VERSION} $TRAVIS_TAG tag

elif [[ ${TRAVIS_BRANCH} =~ ^release\-[0-9]+\.[0-9]+$ ]]; then

    IFS=- read -a ver_number <<< "$TRAVIS_BRANCH"
    BRANCH_VERSION=${ver_number[1]}
    # Release with unified branch and file versions
    git_branch_commit_and_release ${FILE_VERSION} ${BRANCH_VERSION} branch rc

elif [[ $TRAVIS_BRANCH = "develop" ]]; then

    VERSION="alpha"
    release_process

fi
