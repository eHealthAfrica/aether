#!/usr/bin/env bash
set -e

docker-compose build
docker-compose up -d db

docker-compose run core setuplocaldb
docker-compose run core test

docker-compose up -d core-test

docker-compose run odk-importer setuplocaldb
docker-compose run odk-importer test

docker-compose run couchdb-sync setuplocaldb
docker-compose run couchdb-sync test
