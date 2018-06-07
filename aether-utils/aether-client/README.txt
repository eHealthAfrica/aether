This is the official Python Client for the Aether Kernel.

For usage patterns see ./aether/tests/test_client.py

Developing the client:

To distribute changes to the client to other modules, we need to package a new version for each
docker container. We can do that through the build option in ./entrypoint.sh. This needs to be
run in the aether-client docker container. To just build a new wheel in ./dist, from the base
Aether dir run:

    `docker-compose -f ./docker-compose-client.yml run client build`

To build and distribute, there's a script in:

    `scripts/build_aether_utils_and_distribute.sh`
