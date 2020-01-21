#!/usr/bin/env bash
#
# Copyright (C) 2020 by eHealth Africa : http://www.eHealthAfrica.org
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

LINE=`printf -v row "%${COLUMNS:-$(tput cols)}s"; echo ${row// /#}`

DEPLOY_APPS=( kernel odk ui producer )

export GOOGLE_APPLICATION_CREDENTIALS="gcs_key.json"

if [[ ${TRAVIS_TAG} =~ ^[0-9]+(\.[0-9]+){2}$ ]]; then

    echo "${LINE}"
    echo "Skipping production deployment (temporary)"
    echo "${LINE}"
    exit 0

    DOCKER_VERSION=${TRAVIS_TAG}
    GCR_VERSION=${TRAVIS_TAG}
    GCS_PROJECT="eha-data"
    GCR_PROJECT="production-228613"
    RELEASE_BUCKET="aether-releases"

    openssl aes-256-cbc \
        -K $encrypted_17d8de6bf835_key \
        -iv $encrypted_17d8de6bf835_iv \
        -in prod.json.enc \
        -out gcs_key.json \
        -d

elif [[ ${TRAVIS_BRANCH} =~ ^release\-[0-9]+\.[0-9]+$ ]]; then

    echo "${LINE}"
    echo "Skipping release candidates deployment (temporary)"
    echo "${LINE}"
    exit 0

    FILE_VERSION=`cat VERSION`
    DOCKER_VERSION="${FILE_VERSION}-rc"

    GCR_VERSION="${DOCKER_VERSION}-${TRAVIS_COMMIT}"

    # deploy release candidates in ???
    GCS_PROJECT="alpha"
    GCR_PROJECT="development-223016"
    export RELEASE_BUCKET="aether-releases-dev"

else

    DOCKER_VERSION="alpha"
    GCR_VERSION=${TRAVIS_COMMIT}
    GCS_PROJECT="alpha"
    GCR_PROJECT="development-223016"
    export RELEASE_BUCKET="aether-releases-dev"

    openssl aes-256-cbc \
        -K $encrypted_17d8de6bf835_key \
        -iv $encrypted_17d8de6bf835_iv \
        -in dev.json.enc \
        -out gcs_key.json \
        -d
fi

echo "${LINE}"
echo "Docker images:        ${DEPLOY_APPS[@]}"
echo "Docker images tag:    $DOCKER_VERSION"
echo "Deployment version:   $GCR_VERSION"
echo "Repository project:   $GCR_PROJECT"
echo "Storage project:      $GCS_PROJECT"
echo "${LINE}"


# ===========================================================
# install dependencies and create GC credentials files
pip install -q google-cloud-storage push-app-version


# ===========================================================
# pull images from public docker hub

DOCKER_IMAGE_REPO="ehealthafrica"

for APP in "${DEPLOY_APPS[@]}"; do
    AETHER_APP="aether-${APP}"
    SRC_IMG="${DOCKER_IMAGE_REPO}/${AETHER_APP}:${DOCKER_VERSION}"

    echo "Pulling Docker image ${SRC_IMG}"
    docker pull "${SRC_IMG}"
    echo "${LINE}"
done


# ===========================================================
# push images to deployment repository

GCR_REPO_URL="https://eu.gcr.io"
GCR_IMAGE_REPO="eu.gcr.io/${GCR_PROJECT}/aether"

# https://cloud.google.com/container-registry/docs/advanced-authentication#json_key_file
cat gcs_key.json | docker login -u _json_key --password-stdin $GCR_REPO_URL

for APP in "${DEPLOY_APPS[@]}"; do
    AETHER_APP="aether-${APP}"

    SRC_IMG="${DOCKER_IMAGE_REPO}/${AETHER_APP}:${DOCKER_VERSION}"
    DEST_IMG="${GCR_IMAGE_REPO}/${AETHER_APP}:${GCR_VERSION}"

    echo "Pushing GCR image ${DEST_IMG}"
    docker tag "$SRC_IMG" "$DEST_IMG"
    docker push "${DEST_IMG}"
    echo "${LINE}"
done

docker logout ${GCR_REPO_URL} || true


# ===========================================================
# notify to Google Cloud Storage the new images

push-app-version \
    --version $GCR_VERSION \
    --project $GCS_PROJECT
