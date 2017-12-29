#!/bin/bash

echo "Killing ES index for aether-demo-2"
curl -X DELETE "http://localhost:9200/aether-demo-2"

echo "Setting up Project Data"

pipenv --three --where install
pipenv run python ./setup_project.py

echo "You may now submit data to the server"
