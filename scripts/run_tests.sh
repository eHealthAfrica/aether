set -x

docker-compose build kernel

NAMESPACE=test
kubectl create namespace $NAMESPACE
kubectl config set-context $(kubectl config current-context) --namespace=$NAMESPACE

helm del --purge db
helm del --purge kernel
helm del --purge odk

kubectl delete --all pods --namespace=$NAMESPACE
kubectl delete --all deployments --namespace=$NAMESPACE
kubectl delete --all services --namespace=$NAMESPACE
kubectl delete --all secrets --namespace=$NAMESPACE
kubectl delete --all persistentvolumeclaims --namespace=$NAMESPACE
kubectl delete --all persistentvolumes --namespace=$NAMESPACE

kubectl create -f ./helm/dev-secrets/secrets.yaml
kubectl create -f ./helm/dev-secrets/database-secrets.yaml

helm install stable/postgresql --name db --set imageTag=9.6.3,persistence.enabled=false,fullnameOverride=db,postgresPassword=secret,postgresUser=postgres
kubectl rollout status deployment db

helm install --name kernel helm/kernel
kubectl rollout status deployment kernel

# kubectl exec --namespace=$NAMESPACE -it $(kubectl get pods | grep kernel | awk '{print $1}') --container kernel -- bash /code/entrypoint.sh setuplocaldb

# kubectl exec --namespace=$NAMESPACE -it $(kubectl get pods | grep kernel | awk '{print $1}') --container kernel -- bash /code/entrypoint.sh test_coverage
