#!/bin/bash

set -x

NAMESPACE=test

kubectl config set-context $(kubectl config current-context) --namespace=$NAMESPACE

getRecent () {
    kubectl get pods --sort-by=.status.startTime -l app=$1 --no-headers \
        | tail -n 1 \
        | awk '{print $1}'
}

runCommand () {
    local label=$1
    shift
    kubectl exec -it $(getRecent $label) --container $label -- \
            bash /code/entrypoint.sh "${@}"
}

test_kernel () {
    runCommand kernel test
}

test_odk () {
    local fixture=aether/kernel/api/tests/fixtures/project_empty_schema.json
    runCommand kernel manage loaddata $fixture
    runCommand odk test
}

case "$1" in
    test_kernel )
        test_kernel
    ;;

    test_odk )
        test_odk
    ;;

    test_all )
        test_kernel
        test_odk
    ;;

    *)
        show_help
    ;;
esac
