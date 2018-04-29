#!/usr/bin/env bash

set -x

VALUES_DIR=$1

docker-compose build kernel odk

helm install stable/postgresql --name db --values=./helm/overrides/db.yaml
kubectl rollout status deployment db

helm install --name kernel helm/kernel --values=$VALUES_DIR/kernel.yaml
kubectl rollout status deployment kernel

helm install --name odk helm/odk --values=$VALUES_DIR/odk.yaml
kubectl rollout status deployment odk

# helm install stable/postgresql \
#      --name db \
#      --values=./helm/overrides/db.yaml
# kubectl rollout status deployment db

# helm install helm/kernel \
#      --name kernel \
#      --values=./$VALUES_DIR/kernel.yaml
# kubectl rollout status deployment kernel

# helm install helm/odk \
#      --name odk \
#      --values=$VALUES_DIR/odk.yaml
# kubectl rollout status deployment odk
