set -x

NAMESPACE=test

docker-compose build kernel

getRecent () {
    kubectl get pods --sort-by=.status.startTime -l app=$1 --no-headers | tail -n 1 | awk '{print $1}'
}

kubectl exec --namespace=$NAMESPACE -it $(getRecent kernel) --container kernel -- bash /code/entrypoint.sh setuplocaldb

kubectl exec --namespace=$NAMESPACE -it $(getRecent kernel) --container kernel -- bash /code/entrypoint.sh test_coverage
