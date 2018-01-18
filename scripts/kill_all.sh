#!/usr/bin/env bash
set -e

docker-compose kill
docker-compose -f docker-compose-base.yml   kill
docker-compose -f docker-compose-common.yml kill
docker-compose -f docker-compose-kernel.yml kill
docker-compose -f docker-compose-odk.yml    kill
docker-compose -f docker-compose-sync.yml   kill
docker-compose -f docker-compose-test.yml   kill
