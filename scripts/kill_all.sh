#!/usr/bin/env bash
set -Eeuo pipefail

docker-compose kill
docker-compose -f docker-compose-base.yml   kill
docker-compose -f docker-compose-common.yml kill
docker-compose -f docker-compose-test.yml   kill
