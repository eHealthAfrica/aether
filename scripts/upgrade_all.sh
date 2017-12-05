#!/usr/bin/env bash
set -e

containers=( core odk-importer couchdb-sync ui )

# create the common module
echo "_____________________________________________ Building aether.common module"
docker-compose -f docker-compose-test.yml run common-test build
PCK_FILE=aether.common-0.0.0-py2.py3-none-any.whl

for container in "${containers[@]}"
do
  :

  # copy the new common module into the container dependencies
  echo "_____________________________________________ Copying aether.common module in $container"
  cp -r ./aether-common/dist/$PCK_FILE ./aether-$container/conf/pip/dependencies/

  # replace `requirements.txt` file with `primary-requirements.txt` file
  cp ./aether-$container/conf/pip/primary-requirements.txt ./aether-$container/conf/pip/requirements.txt

  echo "_____________________________________________ Building $container"
  # rebuild container
  docker-compose build $container

  # upgrade pip dependencies
  echo "_____________________________________________ Updating $container"
  docker-compose run $container pip_freeze
  echo "_____________________________________________ $container updated!"
done
