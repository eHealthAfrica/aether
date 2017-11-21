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

apt-get update -qq
cat /tmp/apt-packages.txt | xargs apt-get -qq --yes --force-yes install


################################################################################
# last steps and cleaning
################################################################################

apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
