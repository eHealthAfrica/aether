#!/usr/bin/env bash

set -x

# Install secrets.
kubectl create -f ./helm/dev-secrets/secrets.yaml
kubectl create -f ./helm/dev-secrets/database-secrets.yaml
