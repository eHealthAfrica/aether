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

release_process () {
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
    CORE_APPS=( kernel odk couchdb-sync ui )
    CORE_COMPOSE='docker-compose.yml'
    CONNECT_APPS=( producer )
    CONNECT_COMPOSE='docker-compose-connect.yml'

    for APP in "${CORE_APPS[@]}"
    do
        release_app $APP $CORE_COMPOSE
    done

    for CONNECT_APP in "${CONNECT_APPS[@]}"
    do
        release_app $CONNECT_APP $CONNECT_COMPOSE
    done
}

version_compare () {
    if [[ $1 == $2 ]]
    then
        return 0
    fi
    local IFS=.
    local i ver1=($1) ver2=($2)
    # fill empty fields in ver1 with zeros
    for ((i=${#ver1[@]}; i<${#ver2[@]}; i++))
    do
        ver1[i]=0
    done
    for ((i=0; i<${#ver1[@]}; i++))
    do
        if [[ -z ${ver2[i]} ]]
        then
            # fill empty fields in ver2 with zeros
            ver2[i]=0
        fi
        if ((10#${ver1[i]} > 10#${ver2[i]}))
        then
            return 1
        fi
        if ((10#${ver1[i]} < 10#${ver2[i]}))
        then
            return 2
        fi
    done
    return 0
}

function git_branch_commit_and_release() {
    local BRANCH_OR_TAG_VALUE=$2
    local REMOTE=origin COMMIT_BRANCH=$TRAVIS_BRANCH
    if [[ $GITHUB_TOKEN ]]; then
        REMOTE=https://$GITHUB_TOKEN@github.com/$TRAVIS_REPO_SLUG
    else
        echo "Missing environment variable GITHUB_TOKEN=[GitHub Personal Access Token]"
        exit 1
    fi
    version_compare $1 $2
    COMPARE=$?
    if [[ ${COMPARE} = 1 ]]
    then
        echo "VERSION value" $1 "is greater than" $3 "version" $2
    elif [[ ${COMPARE} = 2 ]]
    then
        echo "VERSION value" $1 "is less than" $3 "version" $2
    fi

    for (( p=`grep -o "\."<<<".$BRANCH_OR_TAG_VALUE"|wc -l`; p<3; p++)); do 
        BRANCH_OR_TAG_VALUE+=.0;
        done;
    echo "Setting VERSION to " ${BRANCH_OR_TAG_VALUE}
    
    if [[ $3 = "tag" ]];
    then
        git fetch ${REMOTE} $TRAVIS_BRANCH
        git branch $TRAVIS_BRANCH FETCH_HEAD
        COMMIT_BRANCH=HEAD
    fi

    git checkout $TRAVIS_BRANCH
    echo ${BRANCH_OR_TAG_VALUE} > VERSION
    git add VERSION
    # make Travis CI skip this build
    git commit -m "Version updated to ${BRANCH_OR_TAG_VALUE} [ci skip]"
    if ! git push --quiet --follow-tags ${REMOTE} ${COMMIT_BRANCH} > /dev/null 2>&1; then
        echo "Failed to push git changes to" $TRAVIS_BRANCH
        exit 1
    fi
    if [ ! -z $4 ]; then
        VERSION=${BRANCH_OR_TAG_VALUE}-$4
    fi
    echo "Starting version" ${VERSION} "release"
    release_process

    # Update develop VERSION value to match the latest released version
    git fetch ${REMOTE} develop
    git branch develop FETCH_HEAD
    git checkout develop
    DEV_VERSION=`cat VERSION`
    version_compare ${DEV_VERSION} ${BRANCH_OR_TAG_VALUE}
    COMPARE=$?
    if [[ ${COMPARE} = 2 ]]
    then
        echo "Updating develop branch version to " ${BRANCH_OR_TAG_VALUE}
        echo ${BRANCH_OR_TAG_VALUE} > VERSION
        git add VERSION
        git commit -m "Version updated to ${BRANCH_OR_TAG_VALUE} [ci skip]" #Skip travis build on develop commit
        git push ${REMOTE} develop
    else
        echo "Develop branch VERSION value is not updated"
        echo "New VERSION ${BRANCH_OR_TAG_VALUE} is same or less than develop VERSION ${DEV_VERSION}"
    fi
}

# release version depending on TRAVIS_BRANCH/ TRAVIS_TAG
if [[ $TRAVIS_TAG =~ ^[0-9]+\.[0-9]+[\.0-9]*$ ]]
then
    VERSION=$TRAVIS_TAG
    FILE_VERSION=`cat VERSION`

    # Release with unified branch and file versions
    git_branch_commit_and_release ${FILE_VERSION} $TRAVIS_TAG tag
    exit 0

elif [[ $TRAVIS_BRANCH =~ ^release\-[0-9]+\.[0-9]+[\.0-9]*$ ]]
then
    VERSION=`cat VERSION`
    FILE_VERSION=${VERSION}

    IFS=- read -a ver_number <<< "$TRAVIS_BRANCH"
    BRANCH_VERSION=${ver_number[1]}
    # Release with unified branch and file versions
    git_branch_commit_and_release ${FILE_VERSION} ${BRANCH_VERSION} branch rc
    exit 0
elif [[ $TRAVIS_BRANCH = "develop" ]]
then
    VERSION='alpha'
    release_process
else
    echo "Skipping a release because this branch is not permitted: ${TRAVIS_BRANCH}"
    exit 0
fi
