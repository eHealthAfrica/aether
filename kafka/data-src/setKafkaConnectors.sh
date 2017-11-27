#!/bin/bash
set -e

echo "...Delay before Adding Kafka Connection - AetherDB ..."
sleep 120
echo "...Adding Kafka Connection - AetherDB ..."
curl -X POST -H "Content-Type: application/json" -H "Accept: application/json" -d @/aether/AetherDB.json http://kafka:8083/connectors
