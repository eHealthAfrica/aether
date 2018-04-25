#!/usr/bin/env bash

set -x

NAMESPACE=test

docker-compose build kernel odk

kubectl create namespace $NAMESPACE

kubectl config set-context $(kubectl config current-context) --namespace=$NAMESPACE

kubectl create -f ./helm/dev-secrets/secrets.yaml
kubectl create -f ./helm/dev-secrets/database-secrets.yaml

helm install stable/postgresql --name db --values=./helm/local-db/values.yaml
kubectl rollout status deployment db

helm install --name kernel helm/kernel
kubectl rollout status deployment kernel

helm install --name odk helm/odk
kubectl rollout status deployment odk
