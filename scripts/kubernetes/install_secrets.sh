#!/usr/bin/env bash

set -e

gen_pass() {
    cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1
}

# Install secrets for local development.
kubectl create secret generic database-credentials \
        --from-literal=host=db \
        --from-literal=user=postgres \
        --from-literal=password=$(gen_pass)
kubectl create -f ./helm/test-secrets.yaml
