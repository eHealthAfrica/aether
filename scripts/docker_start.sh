#!/usr/bin/env bash
set -e

# start the indicated app/module with the necessary dependencies
# expected values: kernel, odk, couchdb-sync

# stop all containers
./scripts/kill_all.sh


if [[ $1 = "kernel" ]]
then

  echo "**********************************************************************"
  echo "**** Starting PostgreSQL                                          ****"
  echo "**** Starting NGINX                                               ****"
  echo "**** Starting Kernel app                                          ****"
  echo "**********************************************************************"

  docker-compose up db kernel nginx

elif [[ $1 = "odk" ]]
then

  echo "**********************************************************************"
  echo "**** Starting PostgreSQL                                          ****"
  echo "**** Starting NGINX                                               ****"
  echo "**** Starting Kernel app                                          ****"
  echo "**** Starting ODK module                                          ****"
  echo "**********************************************************************"

  docker-compose up db kernel odk nginx

elif [[ $1 = "couchdb-sync" ]]
then

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

else

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

fi
