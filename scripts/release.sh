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

release_app () {
    APP_NAME=$1
    COMPOSE_PATH=$2
    AETHER_APP="aether-${1}"

    echo "Building Docker image ${IMAGE_REPO}/${AETHER_APP}:${VERSION}"
    docker-compose -f $COMPOSE_PATH build \
        --build-arg GIT_REVISION=$TRAVIS_COMMIT \
        --build-arg VERSION=$VERSION \
        $APP_NAME

    echo "Pushing Docker image ${IMAGE_REPO}/${AETHER_APP}:${VERSION}"
    docker tag ${AETHER_APP} "${IMAGE_REPO}/${AETHER_APP}:${VERSION}"
    docker push "${IMAGE_REPO}/${AETHER_APP}:${VERSION}"

    if [[ $VERSION != "alpha" ]]
    then
        echo "Pushing Docker image ${IMAGE_REPO}/${AETHER_APP}:latest"
        docker tag ${AETHER_APP} "${IMAGE_REPO}/${AETHER_APP}:latest"
        docker push "${IMAGE_REPO}/${AETHER_APP}:latest"
    fi
}

# release version depending on TRAVIS_BRANCH/ TRAVIS_TAG
if [[ $TRAVIS_TAG =~ ^[0-9]+\.[0-9]+[\.0-9]*$ ]]
then
    VERSION=$TRAVIS_TAG

elif [[ $TRAVIS_BRANCH =~ ^release\-[0-9]+\.[0-9]+[\.0-9]*$ ]]
then
    VERSION=`cat VERSION`
    # append "-rc" suffix
    VERSION=${VERSION}-rc

elif [[ $TRAVIS_BRANCH = "develop" ]]
then
    VERSION='alpha'

else
    echo "Skipping a release because this branch is not permitted: ${TRAVIS_BRANCH}"
    exit 0
fi

echo "Release version:  $VERSION"
echo "Release revision: $TRAVIS_COMMIT"

# Login in dockerhub with write permissions (repos are public)
docker login -u $DOCKER_HUB_USER -p $DOCKER_HUB_PASSWORD

# Try to create the aether network+volume if they don't exist.
docker network create aether_internal      2>/dev/null || true
docker volume  create aether_database_data 2>/dev/null || true

# Build dependencies
./scripts/build_aether_utils_and_distribute.sh
./scripts/build_common_and_distribute.sh

# Prepare Aether UI assets
docker-compose build ui-assets
docker-compose run   ui-assets build

# Build docker images
IMAGE_REPO='ehealthafrica'
RELEASE_APPS=( kernel odk couchdb-sync ui producer integration-test )
RELEASE_COMPOSE='docker-compose-release.yml'

for APP in "${RELEASE_APPS[@]}"
do
    release_app $APP $RELEASE_COMPOSE
done
