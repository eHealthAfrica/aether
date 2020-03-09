#!/usr/bin/env sh
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

# create resources directory
mkdir -p ./resources/

# install git (missing in alpine image)
apk add --no-cache git

# get branch and commit from git

# create REVISION resources
GIT_COMMIT=`git rev-parse HEAD`
echo $GIT_COMMIT > ./resources/REVISION

# create VERSION resource (from branch name)
GIT_BRANCH=`git rev-parse --abbrev-ref HEAD`
# replace "release-" prefix with "v" (release-1.2 => v1.2)
GIT_BRANCH=$(echo "$GIT_BRANCH" | sed "s/release-/v/")
if [ $GIT_BRANCH = "develop" ]; then
    echo "alpha" > ./resources/VERSION
else
    echo $GIT_BRANCH > ./resources/VERSION
fi
