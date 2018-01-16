#!/usr/bin/env bash
set -e

docker-compose down
docker-compose -f docker-compose-base.yml   down
docker-compose -f docker-compose-common.yml down
docker-compose -f docker-compose-kernel.yml down
docker-compose -f docker-compose-odk.yml    down
docker-compose -f docker-compose-sync.yml   down
docker-compose -f docker-compose-test.yml   down
