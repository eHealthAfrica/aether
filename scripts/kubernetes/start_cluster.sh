#!/usr/bin/env bash

if [ -z $TRAVIS ]; then
    eval $(minikube docker-env)
fi

set -Eeuo pipefail

# $VALUES_DIR should point to one of the directories in `helm/overrides`. Each
# subdirectory (e.g. "local", "test") represents an environment and contains one
# file for each module with settings for that environment.
VALUES_DIR=$1

# Rebuild all images to make sure that are using the most recent versions.
docker-compose build kernel odk

helm repo add eha https://ehealthafrica.github.io/helm-charts/

# Install the database.
# `name` is not a required parameter, but having named releases is very helpful
# when troubleshooting.
helm install stable/postgresql \
     --name db \
     --values=./helm/overrides/db.yaml \
     --set postgresPassword=$POSTGRES_PASSWORD \
     --version=0.13.1
# Wait for the deployment to reach a "Running" state.
kubectl rollout status deployment db

# Install kernel
helm install eha/kernel \
     --name kernel \
     --values=./$VALUES_DIR/kernel.yaml
# Wait for the deployment to reach a "Running" state.
kubectl rollout status deployment kernel

# Install odk
helm install eha/odk \
     --name odk \
     --values=$VALUES_DIR/odk.yaml
# Wait for the deployment to reach a "Running" state.
kubectl rollout status deployment odk
