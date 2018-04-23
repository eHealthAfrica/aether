set -x

NAMESPACE=test

# docker-compose build
kubectl config set-context $(kubectl config current-context) --namespace=$NAMESPACE

# TODO: better name
getRecent () {
    kubectl get pods --sort-by=.status.startTime -l app=$1 --no-headers | tail -n 1 | awk '{print $1}'
}

kubectl exec --namespace=$NAMESPACE -it $(getRecent kernel) --container kernel -- bash /code/entrypoint.sh setuplocaldb

kubectl exec --namespace=$NAMESPACE -it $(getRecent kernel) --container kernel -- bash /code/entrypoint.sh test_coverage

# kubectl exec -it $(kubectl get pods | grep kernel | awk '{print $1}') --container kernel -- bash /code/entrypoint.sh manage loaddata aether/kernel/api/tests/fixtures/project_empty_schema.json
