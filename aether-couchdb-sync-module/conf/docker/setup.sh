#!/bin/bash
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
set -Eeuox pipefail


################################################################################
# define variables
################################################################################

# Do not buffer stdout so we see log output immediatly
export PYTHONUNBUFFERED=true


################################################################################
# install packages
################################################################################

# install missing packages in slim distribution
apt-get update -qq
apt-get -qq --yes --force-yes install wget gcc

PACKAGE_LIST=/tmp/apt-packages.txt
if [ -f "$PACKAGE_LIST" ]; then
    # Add postgres apt repo to get more recent postgres versions
    echo 'deb http://apt.postgresql.org/pub/repos/apt/ jessie-pgdg main' > /etc/apt/sources.list.d/pgdg.list
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -

    apt-get update -qq
    apt-get -qq --yes --force-yes install `cat $PACKAGE_LIST`
fi

# upgrade pip
pip install --upgrade pip


################################################################################
# last steps and cleaning
################################################################################

apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
