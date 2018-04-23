NAMESPACE=test

kubectl create namespace test

kubectl config set-context $(kubectl config current-context) --namespace=$NAMESPACE

# helm del --purge db
# helm del --purge kernel
# helm del --purge odk

# kubectl delete --all pods --namespace=$NAMESPACE
# kubectl delete --all deployments --namespace=$NAMESPACE
# kubectl delete --all services --namespace=$NAMESPACE
# kubectl delete --all secrets --namespace=$NAMESPACE
# kubectl delete --all persistentvolumeclaims --namespace=$NAMESPACE
# kubectl delete --all persistentvolumes --namespace=$NAMESPACE

# sleep 10;

# kubectl config set-context $(kubectl config current-context) --namespace=test
kubectl get pods

# docker-compose build

# persistence.enable=false for tests

# TODO: bypass getting the id of the running container, instead fire up tests with override commands
# kubectl create -f ./helm/secrets/secrets.yaml
# kubectl create -f ./helm/secrets/database-secrets.yaml

# helm install stable/postgresql --name db --set imageTag=9.6.3,persistence.enabled=false,fullnameOverride=db,postgresPassword=secret,postgresUser=postgres
# kubectl rollout status deployment db --namespace=$NAMESPACE

# helm install ./helm/kernel --name kernel --namespace $NAMESPACE
# kubectl rollout status deployment kernel --namespace=$NAMESPACE

# helm install ./helm/odk --name odk --namespace $NAMESPACE
# kubectl rollout status deployment odk --namespace=$NAMESPACE

# kubectl rollout status deployment db --namespace=$NAMESPACE
# kubectl rollout status deployment kernel --namespace=$NAMESPACE
# kubectl rollout status deployment odk --namespace=$NAMESPACE
