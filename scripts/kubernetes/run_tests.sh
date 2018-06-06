#!/usr/bin/env bash

set -ex

# When stopping and starting pods in a rapid succession, two or more instances
# of a release will be active for a short period of time. To ensure that we run
# the tests in the correct instance, we sort by "status.startTime" and pick the
# most recently started.
get_newest_pod_by_label() {
    kubectl get pods --sort-by=.status.startTime -l app=$1 --no-headers \
        | tail -n 1 \
        | awk '{print $1}'
}

# Run a command in a pod. This assumes that the pod label matches the name of
# the main container inside the pod. This function can not be used to e.g. run a
# command inside the nginx container inside the kernel-<id> pod.
run_command() {
    local label=$1
    shift
    kubectl exec -it $(get_newest_pod_by_label $label) --container $label -- \
            bash /code/entrypoint.sh "${@}"
}

test_kernel() {
    run_command kernel test
}

test_odk() {
    local fixture=aether/kernel/api/tests/fixtures/project_empty_schema.json
    run_command kernel manage loaddata $fixture
    run_command odk test
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
esac
