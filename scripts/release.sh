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
    echo "version: $VERSION"

    echo "Building Docker image ${IMAGE_REPO}/${AETHER_APP}:${VERSION}"
    docker-compose -f $COMPOSE_PATH build \
        --build-arg GIT_REVISION=$TRAVIS_COMMIT \
        --build-arg VERSION=$VERSION \
        $APP_NAME

    docker tag ${AETHER_APP} "${IMAGE_REPO}/${AETHER_APP}:${VERSION}"
    docker tag ${AETHER_APP} "${IMAGE_REPO}/${AETHER_APP}:latest"

    echo "Pushing Docker image ${IMAGE_REPO}/${AETHER_APP}:${VERSION}"
    docker push "${IMAGE_REPO}/${AETHER_APP}:${VERSION}"
    docker push "${IMAGE_REPO}/${AETHER_APP}:latest"
}

# Login in dockerhub
docker login -u ehealthafricadevops -p $DOCKER_HUB_PASSWORD

# Build dependencies
./scripts/build_aether_utils_and_distribute.sh
./scripts/build_common_and_distribute.sh

# Prepare Aether UI assets
docker-compose build ui-assets
docker-compose run   ui-assets build

# Build docker images
IMAGE_REPO='ehealthafrica'
CORE_APPS=( kernel odk couchdb-sync ui )
CORE_COMPOSE='docker-compose.yml'
CONNECT_APPS=( producer )
CONNECT_COMPOSE='docker-compose-connect.yml'
VERSION=`cat VERSION`

if [ -z "$TRAVIS_TAG" ];
then
    VERSION=${VERSION}-rc
fi

for APP in "${CORE_APPS[@]}"
do
    release_app $APP $CORE_COMPOSE
done

for CONNECT_APP in "${CONNECT_APPS[@]}"
do
    release_app $CONNECT_APP $CONNECT_COMPOSE
done
