#!/bin/bash
set -e
set -x


################################################################################
# define variables
################################################################################

# Do not buffer stdout so we see log output immediatly
export PYTHONUNBUFFERED=true


################################################################################
# install packages
################################################################################

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
# create NODE symbolic links
################################################################################

ln -s /usr/local/bin/nodejs                            /usr/local/bin/node
ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js   /usr/local/bin/npm
ln -s /usr/local/lib/node_modules/npm/bin/npx-cli.js   /usr/local/bin/npx


################################################################################
# last steps and cleaning
################################################################################

apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
