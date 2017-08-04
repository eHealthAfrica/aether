#!/usr/bin/env bash
set -e

export DC_TEST=docker-compose-test.yml

docker-compose build
docker-compose -f $DC_TEST build


docker-compose up -d db

docker-compose run core setuplocaldb
docker-compose run core test


docker-compose -f $DC_TEST up -d core-test

docker-compose run odk-importer setuplocaldb
docker-compose run odk-importer test

docker-compose run couchdb-sync setuplocaldb
docker-compose run couchdb-sync test


docker-compose -f $DC_TEST up -d odk-importer-test

docker-compose run ui setuplocaldb
docker-compose run ui test


docker-compose -f $DC_TEST kill odk-importer-test
docker-compose -f $DC_TEST kill core-test
