#!/bin/bash
set -Eeuox pipefail


################################################################################
# define variables
################################################################################

# Do not buffer stdout so we see log output immediatly
export PYTHONUNBUFFERED=true

################################################################################
# last steps and cleaning
################################################################################

apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
