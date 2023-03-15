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
set -Eeuo pipefail


################################################################################
# define variables
################################################################################

POSTGRES_PACKAGE=postgresql-client-11

JVM_ROOT=/usr/lib/jvm
JAVA_FOLDER=java-se-8u41-ri
JAVA_PKG_NAME=openjdk-8u41-b04-linux-x64-14_jan_2020.tar.gz
JAVA_TAR_GZ_URL=https://download.java.net/openjdk/jdk8u41/ri/$JAVA_PKG_NAME


################################################################################
# install packages
################################################################################

# install missing packages of slim distribution and required ones
PACKAGE_LIST=/tmp/apt-packages.txt
if [ -f "$PACKAGE_LIST" ]; then
    apt-get update -qq > /dev/null
    apt-get -qq \
        --yes \
        --allow-downgrades \
        --allow-remove-essential \
        --allow-change-held-packages \
        install `cat $PACKAGE_LIST` > /dev/null
fi

# add postgres apt repo to get more recent postgres versions
echo "deb http://apt.postgresql.org/pub/repos/apt/ `lsb_release -cs`-pgdg main" > /etc/apt/sources.list.d/pgdg.list
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor | tee /etc/apt/trusted.gpg.d/postgresql.gpg
apt-get update -qq > /dev/null
apt-get -qq \
    --yes \
    --allow-downgrades \
    --allow-remove-essential \
    --allow-change-held-packages \
    install $POSTGRES_PACKAGE > /dev/null


# install Java JDK8
echo "Downloading $JAVA_TAR_GZ_URL"
wget -q $JAVA_TAR_GZ_URL
tar -xf $JAVA_PKG_NAME
rm $JAVA_PKG_NAME

mkdir -p /usr/lib/jvm
mv ./$JAVA_FOLDER $JVM_ROOT

update-alternatives --install /usr/bin/java  java  $JVM_ROOT/$JAVA_FOLDER/bin/java  1
update-alternatives --install /usr/bin/javac javac $JVM_ROOT/$JAVA_FOLDER/bin/javac 1
java -version


################################################################################
# Create user and folders
################################################################################

useradd -ms /bin/false aether

mkdir -p /var/run/aether/log/
touch /var/run/aether/uwsgi.pid

chown -Rf aether: /var/run/aether/*
chmod -R 755 /var/run/aether/*


################################################################################
# last steps and cleaning
################################################################################

rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
apt-get clean
apt-get autoremove
