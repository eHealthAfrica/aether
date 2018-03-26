#!/usr/bin/env bash
set -Eeuo pipefail

docker-compose down
docker-compose -f docker-compose-base.yml   down
docker-compose -f docker-compose-common.yml down
docker-compose -f docker-compose-test.yml   down
