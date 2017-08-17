#!/usr/bin/env bash
set -e

containers=( core odk-importer couchdb-sync ui )

for container in "${containers[@]}"
do
  :

  # replace `requirements.txt` file with `primary-requirements.txt` file
  cp ./gather2-$container/conf/pip/primary-requirements.txt ./gather2-$container/conf/pip/requirements.txt

  # rebuild container
  docker-compose build $container

  # upgrade pip dependencies
  docker-compose run $container pip_freeze

done
