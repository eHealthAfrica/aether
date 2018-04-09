#!/bin/bash
set -Eeuox pipefail


################################################################################
# define variables
################################################################################

# Do not buffer stdout so we see log output immediatly
export PYTHONUNBUFFERED=true


################################################################################
# install packages
################################################################################

# Add postgres apt repo to get more recent postgres versions
echo 'deb http://apt.postgresql.org/pub/repos/apt/ jessie-pgdg main' > /etc/apt/sources.list.d/pgdg.list
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -

apt-get update -qq
cat /tmp/apt-packages.txt | xargs apt-get -qq --yes --force-yes install

# upgrade pip
pip install --upgrade pip


################################################################################
# last steps and cleaning
################################################################################

apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
