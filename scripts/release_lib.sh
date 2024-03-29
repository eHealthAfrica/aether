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


LINE=`printf -v row "%${COLUMNS:-$(tput cols)}s"; echo ${row// /#}`

IMAGE_REPO="ehealthafrica"
RELEASE_APPS=( kernel exm odk ui producer integration-test )

function build_app {
    APP_NAME=$1

    echo ""
    echo "Building Docker container $APP_NAME"
    docker build \
        --tag aether-${APP} \
        --file ./scripts/deployment/${APP}.Dockerfile \
        .
    echo "${LINE}"
    echo ""
}

function release_app {
    APP_NAME=$1
    APP_TAG=$2
    AETHER_APP="aether-${APP_NAME}"

    echo ""
    echo "Pushing Docker image ${IMAGE_REPO}/${AETHER_APP}:${APP_TAG}"
    docker tag ${AETHER_APP} "${IMAGE_REPO}/${AETHER_APP}:${APP_TAG}"
    docker push "${IMAGE_REPO}/${AETHER_APP}:${APP_TAG}"
    echo "${LINE}"
    echo ""
}

function log_process {
    echo ""
    echo "${LINE}"
    echo "Release version:   $VERSION"
    echo "Release revision:  $TRAVIS_COMMIT"
    echo "Images repository: $IMAGE_REPO"
    echo "Images:            ${RELEASE_APPS[@]}"
    echo "${LINE}"
    echo ""
}

function release_process {
    log_process

    # Login in dockerhub with write permissions (repos are public)
    docker login -u $DOCKER_HUB_USER -p $DOCKER_HUB_PASSWORD

    for APP in "${RELEASE_APPS[@]}"; do
        build_app $APP
        release_app $APP $VERSION
    done
}

# Usage: increment_version <version> [<position>]
function increment_version {
    local v=$1
    if [ -z $2 ]; then
        local rgx='^((?:[0-9]+\.)*)([0-9]+)($)'
    else
        local rgx='^((?:[0-9]+\.){'$(($2-1))'})([0-9]+)(\.|$)'
        for (( p=`grep -o "\."<<<".$v"|wc -l`; p<$2; p++)); do
            v+=.0;
        done;
    fi
    val=`echo -e "$v" | perl -pe 's/^.*'$rgx'.*$/$2/'`
    TAG_INCREASED_VERSION=$(echo "$v" | perl -pe s/$rgx.*$'/${1}'`printf %0${#val}s $(($val+1))`/)
}

function version_compare {
    if [[ $1 == $2 ]]; then
        # version on file and (branch | tag) versions are equal
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
            # version on file is greater than (branch | tag) version
            return 1
        fi
        if ((10#${ver1[i]} < 10#${ver2[i]}))
        then
            # version on file is less than (branch | tag) version
            return 2
        fi
    done

    return 0
}

function git_branch_commit_and_release {
    # Evaluates the VERSION file, increases the version value if its a tag and commit changes to base branch
    # Expected Args:
    ## <VERSION_ON_FILE> <VERSION_FROM_BRANCH/TAG> <BRANCH_TYPE> <IS_RC>
    ### VERSION_ON_FILE : The version value read from the VERSION file
    ### VERSION_FROM_BRANCH/TAG : version value retrieved from the branch name (TRAVIS_TAG / TRAVIS_BRANCH)
    ### BRANCH_TYPE : branch type (options: "branch", "tag")
    ### IS_RC: (optional) if a release candidate should be released (options : "rc")

    local BRANCH_OR_TAG_VALUE=$2
    local REMOTE=origin COMMIT_BRANCH=$TRAVIS_BRANCH
    if [[ $GITHUB_TOKEN ]]; then
        REMOTE=https://$GITHUB_TOKEN@github.com/$TRAVIS_REPO_SLUG
    else
        echo ""
        echo "${LINE}"
        echo "Missing environment variable GITHUB_TOKEN=[GitHub Personal Access Token]"
        echo "${LINE}"
        echo ""
        exit 1
    fi

    if [[ $3 = "branch" ]]; then
        for (( p=`grep -o "\."<<<".$BRANCH_OR_TAG_VALUE"|wc -l`; p<3; p++)); do
            BRANCH_OR_TAG_VALUE+=.0;
        done;

        version_compare $1 $BRANCH_OR_TAG_VALUE
        COMPARE=$?
        if [[ ${COMPARE} = 1 ]]; then
            echo "VERSION value" $1 "is greater than" $3 "version" $2
            BRANCH_OR_TAG_VALUE=$1
        fi

        if [[ -z $VERSION ]]; then
            echo "No VERSION file found, creating one and setting value to ${BRANCH_OR_TAG_VALUE}"
            VERSION=$BRANCH_OR_TAG_VALUE

            git checkout $TRAVIS_BRANCH
            echo ${BRANCH_OR_TAG_VALUE} > VERSION
            git add VERSION
            # make Travis CI skip this build
            COMMIT_MESSAGE="chore: Create VERSION file ${BRANCH_OR_TAG_VALUE} [ci skip]"
            git commit -m "${COMMIT_MESSAGE}"
            if ! git push --quiet --follow-tags ${REMOTE} ${COMMIT_BRANCH} > /dev/null 2>&1; then
                echo ""
                echo "${LINE}"
                echo "Failed to push git changes to" $TRAVIS_BRANCH
                echo "${LINE}"
                echo ""
                exit 1
            fi
        fi

    elif [[ $3 = "tag" ]]; then
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

        echo "VERSION file set to ${BRANCH_OR_TAG_VALUE} on ${TRAVIS_BRANCH} branch"

        git checkout $TRAVIS_BRANCH
        echo ${BRANCH_OR_TAG_VALUE} > VERSION
        git add VERSION
        # make Travis CI skip this build
        COMMIT_MESSAGE="chore: Update VERSION file to ${BRANCH_OR_TAG_VALUE} [ci skip]"
        git commit -m "${COMMIT_MESSAGE}"
        if ! git push --quiet --follow-tags ${REMOTE} ${COMMIT_BRANCH} > /dev/null 2>&1; then
            echo ""
            echo "${LINE}"
            echo "Failed to push git changes to" $TRAVIS_BRANCH
            echo "${LINE}"
            echo ""
            exit 1
        fi
    fi

    if [ ! -z $4 ]; then
        VERSION=${BRANCH_OR_TAG_VALUE}-$4
    fi

    echo ""
    echo "${LINE}"
    echo "Starting version" ${VERSION} "release"
    echo "${LINE}"
    echo ""
    release_process
}
