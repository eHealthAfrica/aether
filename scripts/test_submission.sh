#!/usr/bin/env bash

. ./.env

program=$(cat <<EOF
from aether.kernel.api.tests.utils.generators import generate_project
project = generate_project()
print(str(project.mappingsets.first().id))
EOF
)

mappingSetId=$(docker-compose run kernel manage shell -c "$program" | tail -n1 | tr '\r' ' ')

template=$(cat <<EOF
{
 "attachments": [],
 "revision": "1",
 "payload": {
    "test_field": "testing"
 },
 "mappingset": null
}
EOF
)

submission=$(echo "$template" | jq --arg mappingSetId $mappingSetId '.mappingset = $mappingSetId')

function run () {
    for i in {1..50};
    do curl kernel.aether.local:8000/submissions/ \
            -u "$KERNEL_ADMIN_USERNAME:$KERNEL_ADMIN_PASSWORD" \
            -H "Content-Type: application/json" \
            -d "$submission" > /dev/null
    done
}

time run
