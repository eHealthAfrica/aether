#!/usr/bin/env bash

set -x

docker-compose build kernel odk

kubectl create -f ./helm/dev-secrets/secrets.yaml
kubectl create -f ./helm/dev-secrets/database-secrets.yaml

VALUES_DIR=$1

helm install stable/postgresql --name db --values=./helm/overrides/db.yaml
kubectl rollout status deployment db

helm install --name kernel helm/kernel --values=$VALUES_DIR/kernel.yaml
kubectl rollout status deployment kernel

helm install --name odk helm/odk --values=$VALUES_DIR/odk.yaml
kubectl rollout status deployment odk
