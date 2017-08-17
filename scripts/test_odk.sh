#!/usr/bin/env bash
set -e

export DC_TEST=docker-compose-test.yml

docker-compose up -d db

docker-compose -f $DC_TEST run core-test setuplocaldb
docker-compose -f $DC_TEST up -d core-test

docker-compose run odk-importer test

docker-compose -f $DC_TEST kill core-test
