# kubectl exec -it $(kubectl get pods | grep kernel | awk '{print $1}') --container kernel -- bash /code/entrypoint.sh test_coverage

# set -Eeux

# kubectl create namespace test

# kubectl exec --namespace=test -it $(kubectl get pods | grep kernel | awk '{print $1}') --container kernel -- bash /code/entrypoint.sh setuplocaldb

# kubectl exec --namespace=test -it $(kubectl get pods | grep kernel | awk '{print $1}') --container kernel -- bash /code/entrypoint.sh test_coverage

set -x

helm upgrade kernel helm/kernel --recreate-pods
helm upgrade odk helm/odk --recreate-pods

kubectl rollout status deployment kernel
kubectl rollout status deployment odk

# DC_COMMON="docker-compose -f docker-compose-common.yml"
# $DC_COMMON down
# $DC_COMMON build
# $DC_COMMON run common test

# getRunningPod () {
#     APPLABEL=$1
#     JQ_EXPR='.items [] | select(.status.phase=="Running") | select(.metadata.labels.app=="$APPLABEL").metadata.labels.app'
#     kubectl get pods -o json | jq '.items [] | select(.status.phase=="Running") | select(.metadata.labels.app=="$APPLABEL").metadata.labels.app'
# }

# echo $(getRunningPod kernel)

# kubectl get pods -o json | jq '.items [] | select(.status.phase=="Running") | select(.metadata.labels.app=="kernel").metadata.name'

# kubectl exec -it $(kubectl get pods | grep kernel | awk '{print $1}') --container kernel -- bash /code/entrypoint.sh manage loaddata aether/kernel/api/tests/fixtures/project_empty_schema.json

# kubectl exec -it $(kubectl get pods | grep odk | awk '{print $1}') --container odk -- bash /code/entrypoint.sh manage test aether.odk.api.tests.test_views_submission.PostSubmissionTests.test__submission__post

# kubectl exec -it $(kubectl get pods | grep odk | awk '{print $1}') --container odk -- bash /code/entrypoint.sh manage test

# kubectl exec -it $(kubectl get pods | grep odk | awk '{print $1}') --container odk -- bash /code/entrypoint.sh manage test

