#!/bin/bash
set -Eeuo pipefail

DC_COMMON="docker-compose -f docker-compose-common.yml"

# remove previous containers (clean start)
./scripts/kill_all.sh
$DC_COMMON down

# create the distribution
$DC_COMMON build common
$DC_COMMON run   common build

PCK_FILE=aether.common-0.0.0-py2.py3-none-any.whl

# distribute within the containers
FOLDERS=( aether-kernel aether-odk-module aether-couchdb-sync-module aether-ui )
for FOLDER in "${FOLDERS[@]}"
do
  cp -r ./aether-common-module/dist/$PCK_FILE ./$FOLDER/conf/pip/dependencies/
done

./scripts/kill_all.sh
