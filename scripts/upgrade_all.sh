#!/usr/bin/env bash
set -e

containers=( kernel odk-importer couchdb-sync )

# create the common module
./scripts/build_common_and_distribute.sh


for container in "${containers[@]}"
do
  :

  # replace `requirements.txt` file with `primary-requirements.txt` file
  cp ./aether-$container/conf/pip/primary-requirements.txt ./aether-$container/conf/pip/requirements.txt

  echo "_____________________________________________ Building $container"
  # rebuild container
  docker-compose build $container

  # upgrade pip dependencies
  echo "_____________________________________________ Updating $container"
  docker-compose run $container pip_freeze

  echo "_____________________________________________ Rebuilding $container with updates"
  # rebuild container
  docker-compose build $container

  echo "_____________________________________________ $container updated and rebuilt!"
done

./scripts/kill_all.sh
