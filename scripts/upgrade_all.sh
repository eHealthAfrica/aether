#!/usr/bin/env bash
set -e

# upgrade all containers
docker-compose run core         pip_freeze
docker-compose run odk-importer pip_freeze
docker-compose run couchdb-sync pip_freeze
