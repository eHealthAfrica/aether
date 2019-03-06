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

set -Eo pipefail

function prepare_dependencies {
    ./scripts/build_docker_assets.sh
    ./scripts/build_common_and_distribute.sh
    ./scripts/build_client_and_distribute.sh

    build_app ui-assets
    docker-compose run ui-assets build
}

function build_app {
    APP_NAME=$1
    DC="docker-compose -f docker-compose.yml -f docker-compose-connect.yml -f docker-compose-test.yml"

    echo "Building Docker container $APP_NAME"
    $DC build \
        --no-cache --force-rm --pull \
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

release_process () {

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
}

# Usage: increment_version <version> [<position>]
increment_version () {
    local v=$1
    if [ -z $2 ]; then 
        local rgx='^((?:[0-9]+\.)*)([0-9]+)($)'
    else 
        local rgx='^((?:[0-9]+\.){'$(($2-1))'})([0-9]+)(\.|$)'
        for (( p=`grep -o "\."<<<".$v"|wc -l`; p<$2; p++)); do 
            v+=.0; done;
    fi
    val=`echo -e "$v" | perl -pe 's/^.*'$rgx'.*$/$2/'`
    TAG_INCREASED_VERSION=$(echo "$v" | perl -pe s/$rgx.*$'/${1}'`printf %0${#val}s $(($val+1))`/)
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
        major=0
        minor=0
        # break down the version number into it's components
        regex="([0-9]+).([0-9]+).([0-9]+)"
        if [[ $BRANCH_OR_TAG_VALUE =~ $regex ]]; then
            major="${BASH_REMATCH[1]}"
            minor="${BASH_REMATCH[2]}"
        fi
        TRAVIS_BRANCH="release-${major}.${minor}"
        git fetch ${REMOTE} $TRAVIS_BRANCH
        git branch $TRAVIS_BRANCH FETCH_HEAD
        COMMIT_BRANCH=HEAD
        increment_version $BRANCH_OR_TAG_VALUE 3
        BRANCH_OR_TAG_VALUE=$TAG_INCREASED_VERSION
        echo "Version incremented to ${BRANCH_OR_TAG_VALUE}"
    fi

    git checkout $TRAVIS_BRANCH
    echo ${BRANCH_OR_TAG_VALUE} > VERSION
    git add VERSION
    # make Travis CI skip this build
    COMMIT_MESSAGE="chore: Update VERSION file to ${BRANCH_OR_TAG_VALUE} [ci skip]"
    git commit -m "${COMMIT_MESSAGE}"
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
        git commit -m "${COMMIT_MESSAGE}" #Skip travis build on develop commit
        git push ${REMOTE} develop
    else
        echo "Develop branch VERSION value is not updated"
        echo "New VERSION ${BRANCH_OR_TAG_VALUE} is same or less than develop VERSION ${DEV_VERSION}"
    fi
}

TAG_INCREASED_VERSION="0.0.0"

# release version depending on TRAVIS_BRANCH/ TRAVIS_TAG
if [[ $TRAVIS_TAG =~ ^[0-9]+\.[0-9]+[\.0-9]*$ ]]
then
    VERSION=$TRAVIS_TAG
    FILE_VERSION=`cat VERSION`

    # Release with unified branch and file versions
    git_branch_commit_and_release ${FILE_VERSION} $TRAVIS_TAG tag

elif [[ $TRAVIS_BRANCH =~ ^release\-[0-9]+\.[0-9]+[\.0-9]*$ ]]
then
    VERSION=`cat VERSION`
    FILE_VERSION=${VERSION}

    IFS=- read -a ver_number <<< "$TRAVIS_BRANCH"
    BRANCH_VERSION=${ver_number[1]}
    # Release with unified branch and file versions
    git_branch_commit_and_release ${FILE_VERSION} ${BRANCH_VERSION} branch rc
elif [[ $TRAVIS_BRANCH = "develop" ]]
then
    VERSION='alpha'
    release_process
else
    echo "Skipping a release because this branch is not permitted: ${TRAVIS_BRANCH}"
fi
