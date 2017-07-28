#!/usr/bin/env bash
set -ex

echo "-------------------------------------------------------------------------"
echo "Building containers..."
docker-compose build
echo " OK. "

echo "-------------------------------------------------------------------------"
echo "Start database container..."
docker-compose up -d db
echo " OK. "

echo "-------------------------------------------------------------------------"
echo "Preparing containers..."
docker-compose run core setuplocaldb
docker-compose run odk-importer setuplocaldb
docker-compose run couchdb-sync setuplocaldb
echo " OK. "

echo "-------------------------------------------------------------------------"
echo "Testing Gather2 Core..."
docker-compose run core test
echo " OK. "

echo "-------------------------------------------------------------------------"
echo "Testing Gather2 ODK..."
docker-compose run odk-importer test
echo " OK. "

echo "-------------------------------------------------------------------------"
echo "Testing Gather2 Sync..."
docker-compose run couchdb-sync test
echo " OK. "
