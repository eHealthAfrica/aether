#!/bin/bash
pushd ..
echo "\nKilling Aether (&DB)"
docker-compose down
docker-compose down
echo "\nRecreating Aether (&DB)"
docker-compose up -d
popd

echo "\nwaiting 20 seconds while the pipe flushes..."
sleep 20

./reset_demo.sh



