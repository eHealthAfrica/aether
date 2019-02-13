#!/usr/bin/env bash

set -Eeuo pipefail

# Install secrets for local development.
kubectl create secret generic database-credentials \
        --from-literal=host=db \
        --from-literal=user=postgres \
        --from-literal=password=$POSTGRES_PASSWORD
kubectl create -f ./helm/test-secrets.yaml
