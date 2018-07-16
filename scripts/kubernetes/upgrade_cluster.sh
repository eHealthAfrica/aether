#!/usr/bin/env bash

set -Eeuo pipefail

VALUES_DIR=$1

docker-compose build kernel odk

helm upgrade \
     --install db stable/postgresql \
     --values=./helm/overrides/db.yaml
kubectl rollout status deployment db

helm upgrade \
     --install kernel helm/kernel \
     --values=./$VALUES_DIR/kernel.yaml
kubectl rollout status deployment kernel

helm upgrade \
     --install odk helm/odk \
     --values=$VALUES_DIR/odk.yaml
kubectl rollout status deployment odk
