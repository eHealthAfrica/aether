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

function pull_images {
    for APP in "${DEPLOY_APPS[@]}"; do
        AETHER_APP="aether-${APP}"
        SRC_IMG="${DOCKER_IMAGE_REPO}/${AETHER_APP}:${DOCKER_VERSION}"

        echo "Pulling Docker image ${SRC_IMG}"
        docker pull "${SRC_IMG}"
        echo "${LINE}"
    done
}

function push_images {
    for APP in "${DEPLOY_APPS[@]}"; do
        AETHER_APP="aether-${APP}"

        SRC_IMG="${DOCKER_IMAGE_REPO}/${AETHER_APP}:${DOCKER_VERSION}"
        DEST_IMG="${GCR_IMAGE_REPO}/${AETHER_APP}:${GCS_VERSION}"

        echo "Pushing GCS image ${DEST_IMG}"
        docker tag "$SRC_IMG" "$DEST_IMG"
        docker push "${DEST_IMG}"
        echo "${LINE}"
    done
}

LINE=`printf -v row "%${COLUMNS:-$(tput cols)}s"; echo ${row// /#}`

if [[ ${TRAVIS_TAG} =~ ^[0-9]+(\.[0-9]+){2}$ ]]; then

    echo "${LINE}"
    echo "Skipping production deployment (temporary)"
    exit 0

    # DOCKER_VERSION=${TRAVIS_TAG}
    # GCS_VERSION=${TRAVIS_TAG}
    # GCS_PROJECTS="eha-data"

elif [[ ${TRAVIS_BRANCH} =~ ^release\-[0-9]+\.[0-9]+$ ]]; then

    echo "${LINE}"
    echo "Skipping release candidates deployment"
    exit 0

    # FILE_VERSION=`cat VERSION`
    # DOCKER_VERSION="${FILE_VERSION}-rc"

    # GCS_VERSION="${DOCKER_VERSION}-${TRAVIS_COMMIT}"
    # # deploy release candidates in ???
    # GCS_PROJECTS="alpha"

else

    DOCKER_VERSION="alpha"
    GCS_VERSION=${TRAVIS_COMMIT}
    GCS_PROJECTS="alpha"

fi

DOCKER_IMAGE_REPO="ehealthafrica"

DEPLOY_APPS=( kernel odk ui producer )

export RELEASE_BUCKET="aether-releases"
export GOOGLE_APPLICATION_CREDENTIALS="gcs_key.json"

echo "${LINE}"
echo "Docker images tag:   $DOCKER_VERSION"
echo "Deployment version:  $GCS_VERSION"
echo "Deployment project:  $GCS_PROJECTS"
echo "Images:              ${DEPLOY_APPS[@]}"
echo "${LINE}"


# ===========================================================
# install dependencies and create GCS credentials files
openssl aes-256-cbc \
    -K $encrypted_9112fb2807d4_key \
    -iv $encrypted_9112fb2807d4_iv \
    -in gcs_key.json.enc \
    -out gcs_key.json \
    -d

pip install -q google-cloud-storage push-app-version

# ===========================================================
# pull images from public docker hub

# Note: pulling only the alpha images (tags are already in docker hub)
if [[ $TRAVIS_BRANCH = "develop" ]]; then
    pull_images
fi

# ===========================================================
# push images to deployment repository

### GCR_URL="https://eu.gcr.io"
### GCR_IMAGE_REPO="eu.gcr.io/${GCS_PROJECTS}"
GCR_IMAGE_REPO=${DOCKER_IMAGE_REPO}

### docker login -u _json_key -p "$(cat gcs_key.json)" ${GCR_URL}

# Note: pushing only the alpha commit (tags are already in docker hub)
if [[ $TRAVIS_BRANCH = "develop" ]]; then
    docker login -u $DOCKER_HUB_USER -p $DOCKER_HUB_PASSWORD

    push_images
fi

### docker logout ${GCR_URL} || true

# ===========================================================
# notify to Google Cloud Storage the new images

python ./scripts/push_version.py \
    --version $GCS_VERSION \
    --projects $GCS_PROJECTS
