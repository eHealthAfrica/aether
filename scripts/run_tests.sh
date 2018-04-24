set -x

NAMESPACE=test

# docker-compose build
kubectl config set-context $(kubectl config current-context) --namespace=$NAMESPACE

# TODO: better name
getRecent () {
    kubectl get pods --sort-by=.status.startTime -l app=$1 --no-headers | tail -n 1 | awk '{print $1}'
}

# TODO:
# load other service if not exists
# test_kernel
# test_odk
# test_x

kubectl exec --namespace=$NAMESPACE -it $(getRecent kernel) --container kernel -- bash /code/entrypoint.sh setuplocaldb

kubectl exec --namespace=$NAMESPACE -it $(getRecent kernel) --container kernel -- bash /code/entrypoint.sh test

kubectl exec -it $(getRecent kernel) --container kernel -- bash /code/entrypoint.sh manage loaddata aether/kernel/api/tests/fixtures/project_empty_schema.json

kubectl exec --namespace=$NAMESPACE -it $(getRecent odk) --container odk -- bash /code/entrypoint.sh test

