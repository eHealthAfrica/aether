#!/usr/bin/env bash
set -e

docker-compose kill
docker-compose -f docker-compose-test.yml kill
docker-compose -f docker-compose-common.yml kill
