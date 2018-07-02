#!/usr/bin/env bash

set -x

# $VALUES_DIR should point to one of the directories in `helm/overrides`. Each
# subdirectory (e.g. "local", "test") represents an environment and contains one
# file for each module with settings for that environment.
VALUES_DIR=$1
eval $(minikube docker-env)

# Rebuild all images to make sure that are using the most recent versions.
docker-compose build kernel odk

# Install the database.
# `name` is not a required parameter, but having named releases is very helpful
# when troubleshooting.
helm install stable/postgresql \
     --name db \
     --values=./helm/overrides/db.yaml \
     --version=0.13.1
# Wait for the deployment to reach a "Running" state.
kubectl rollout status deployment db

# Install kernel
helm install helm/kernel \
     --name kernel \
     --values=./$VALUES_DIR/kernel.yaml
# Wait for the deployment to reach a "Running" state.
kubectl rollout status deployment kernel

# Install odk
helm install helm/odk \
     --name odk \
     --values=$VALUES_DIR/odk.yaml
# Wait for the deployment to reach a "Running" state.
kubectl rollout status deployment odk
