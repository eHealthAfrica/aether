#!/usr/bin/env bash
set -Eeuo pipefail

docker-compose 							kill
docker-compose -f docker-compose-base.yml      			kill
docker-compose -f docker-compose-connect.yml   			kill
docker-compose -f docker-compose-common.yml    			kill
docker-compose -f docker-compose-build-aether-utils.yml    	kill
docker-compose -f docker-compose-test.yml      			kill
