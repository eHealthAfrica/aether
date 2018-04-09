#!/usr/bin/env bash

# start the indicated app/module with the necessary dependencies
#
#   docker_start.sh [--force | -f] [--build | -b] <app>
#
# arguments:
#   --force | -f  will kill running containers
#   --build | -b  will build containers

#   <app>
#      Expected values: kernel, odk, couchdb-sync or sync.
#      Any other value will start all containers.
#

# default values
kill=no
build=no
container=all

while [[ $# -gt 0 ]]
do
  case "$1" in
    -f|--force)
      # stop all containers
      kill=yes

      shift # past argument
    ;;

    -b|--build)
      # build all containers
      build=yes

      shift # past argument
    ;;

    *)
      # otherwise is the container name
      container="$1"

      shift # past argument
    ;;
  esac
done


# just show what's running
echo ""
docker-compose ps
echo ""


if [[ $kill = "yes" ]]
then
  echo "**********************************************************************"
  echo "**** Killing containers                                           ****"
  echo "**********************************************************************"

  ./scripts/kill_all.sh
fi


if [[ $build = "yes" ]]
then
  echo "**********************************************************************"
  echo "**** Building containers                                          ****"
  echo "**********************************************************************"

  docker-compose build
fi


case $container in

  kernel)
    echo "**********************************************************************"
    echo "**** Starting PostgreSQL                                          ****"
    echo "**** Starting NGINX                                               ****"
    echo "**** Starting Kernel app                                          ****"
    echo "**********************************************************************"

    docker-compose up db kernel nginx
  ;;

  odk)
    echo "**********************************************************************"
    echo "**** Starting PostgreSQL                                          ****"
    echo "**** Starting NGINX                                               ****"
    echo "**** Starting Kernel app                                          ****"
    echo "**** Starting ODK module                                          ****"
    echo "**********************************************************************"

    docker-compose up db kernel odk nginx
  ;;

  sync|couchdb-sync)
    echo "**********************************************************************"
    echo "**** Starting PostgreSQL                                          ****"
    echo "**** Starting CouchDB                                             ****"
    echo "**** Starting Redis                                               ****"
    echo "**** Starting RQ                                                  ****"
    echo "**** Starting NGINX                                               ****"
    echo "**** Starting Kernel app                                          ****"
    echo "**** Starting CouchDB-Sync module                                 ****"
    echo "**********************************************************************"

    docker-compose up db couchdb redis kernel couchdb-sync couchdb-sync-rq nginx
  ;;

  ui)
    echo "**********************************************************************"
    echo "**** Starting PostgreSQL                                          ****"
    echo "**** Starting NGINX                                               ****"
    echo "**** Starting Kernel app                                          ****"
    echo "**** Starting UI module                                           ****"
    echo "**** Starting webpack                                             ****"
    echo "**********************************************************************"

    docker-compose up db kernel ui webpack nginx
  ;;

  *)
    echo "**********************************************************************"
    echo "**** Starting PostgreSQL                                          ****"
    echo "**** Starting CouchDB                                             ****"
    echo "**** Starting Redis                                               ****"
    echo "**** Starting RQ                                                  ****"
    echo "**** Starting NGINX                                               ****"
    echo "**** Starting Kernel app                                          ****"
    echo "**** Starting ODK module                                          ****"
    echo "**** Starting CouchDB-Sync module                                 ****"
    echo "**********************************************************************"

    docker-compose up
  ;;

esac
