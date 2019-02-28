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

function prepare_dependencies {
    ./scripts/build_docker_assets.sh
    ./scripts/build_common_and_distribute.sh
    ./scripts/build_client_and_distribute.sh

    docker-compose build ui-assets
    docker-compose run   ui-assets build
}

function build_app {
    APP_NAME=$1
    DC="docker-compose -f docker-compose.yml -f docker-compose-connect.yml -f docker-compose-test.yml"

    echo "Building Docker container $APP_NAME"
    $DC build \
        --build-arg GIT_REVISION=$TRAVIS_COMMIT \
        --build-arg VERSION=$VERSION \
        $APP_NAME
    echo "_____________________________________________"
}

function release_app {
    APP_NAME=$1
    AETHER_APP="aether-${APP_NAME}"

    echo "Pushing Docker image ${IMAGE_REPO}/${AETHER_APP}:${VERSION}"
    docker tag ${AETHER_APP} "${IMAGE_REPO}/${AETHER_APP}:${VERSION}"
    docker push "${IMAGE_REPO}/${AETHER_APP}:${VERSION}"

    if [[ $VERSION != "alpha" ]]
    then
        echo "Pushing Docker image ${IMAGE_REPO}/${AETHER_APP}:latest"
        docker tag ${AETHER_APP} "${IMAGE_REPO}/${AETHER_APP}:latest"
        docker push "${IMAGE_REPO}/${AETHER_APP}:latest"
    fi
    echo "_____________________________________________"
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

# Login in dockerhub with write permissions (repos are public)
docker login -u $DOCKER_HUB_USER -p $DOCKER_HUB_PASSWORD

IMAGE_REPO='ehealthafrica'
RELEASE_APPS=( kernel odk couchdb-sync ui producer integration-test )

echo "_____________________________________________"
echo "Release version:   $VERSION"
echo "Release revision:  $TRAVIS_COMMIT"
echo "Images repository: $IMAGE_REPO"
echo "Images:            ${RELEASE_APPS[@]}"
echo "_____________________________________________"

prepare_dependencies

for APP in "${RELEASE_APPS[@]}"
do
    build_app $APP
    release_app $APP
done
