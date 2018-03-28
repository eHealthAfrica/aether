#!/usr/bin/env bash
set -Eeuo pipefail

containers=( kernel odk couchdb-sync ui )

# create the common module
./scripts/build_common_and_distribute.sh


for container in "${containers[@]}"
do
  :
  # FIXME: we need a better strategy for this. As soon as all aether modules are
  # named in a consistent way (e.g. "aether-<module-name>"), the below
  # conditionals can be removed.
  if [[ $container = "kernel" || container = "ui" ]]
  then
    FOLDER=aether-$container
  else
    FOLDER=aether-$container-module
  fi
  PIP_FOLDER=./$FOLDER/conf/pip
  # replace `requirements.txt` file with `primary-requirements.txt` file
  cp $PIP_FOLDER/primary-requirements.txt $PIP_FOLDER/requirements.txt

  echo "_____________________________________________ Building $container"
  # force rebuild container
  docker-compose build --no-cache --force-rm $container

  # upgrade pip dependencies
  echo "_____________________________________________ Updating $container"
  docker-compose run $container pip_freeze

  echo "_____________________________________________ Rebuilding $container with updates"
  # rebuild container
  docker-compose build --no-cache $container

  echo "_____________________________________________ $container updated and rebuilt!"
done

./scripts/kill_all.sh
