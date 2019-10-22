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

set -Eo pipefail

LINE="-------------------------------------------------------------------------"

GIT_COMMIT=$CIRCLE_SHA1
GIT_BRANCH=$CIRCLE_BRANCH
GIT_TAG=$CIRCLE_TAG


if [[ ${GIT_TAG} =~ ^[0-9]+(\.[0-9]+){2}$ ]]; then

    VERSION=$GIT_TAG

elif [[ ${GIT_BRANCH} =~ ^release\-[0-9]+\.[0-9]+$ ]]; then

    FILE_VERSION=`cat VERSION`
    VERSION="${FILE_VERSION}-rc"

elif [[ $GIT_BRANCH = "develop" ]]; then

    VERSION="alpha"

# else

#     echo "Not permitted"
#     exit 1

fi

openssl aes-256-cbc \
    -K $encrypted_9112fb2807d4_key \
    -iv $encrypted_9112fb2807d4_iv \
    -in ./.circleci/gcs_key.json.enc \
    -out ./.circleci/gcs_key.json \
    -d

pip install --user -q google-cloud-storage

# notify to Google Cloud Storage the new image
export RELEASE_BUCKET="aether-releases"
export GOOGLE_APPLICATION_CREDENTIALS="./.circleci/gcs_key.json"

if [ -z "$GIT_TAG" ]; then
    GCS_VERSION="${VERSION}--${GIT_COMMIT}"
else
    GCS_VERSION=$VERSION
fi

if [ "$VERSION" == "alpha" ]; then
    GCS_PROJECTS="alpha"
else
    GCS_PROJECTS="eha-data"
fi

echo "$LINE"
echo "Github repo:    $GIT_REPO"
echo "Github commit:  $GIT_COMMIT"
echo "Github branch:  $GIT_BRANCH"
echo "Github tag:     $GIT_TAG"
echo "$LINE"
echo "Deploying ${VERSION} release"
echo "$LINE"

python ./.circleci/push_version.py --version $GCS_VERSION --projects $GCS_PROJECTS
