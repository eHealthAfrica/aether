#!/usr/bin/env bash

export CHANGE_MINIKUBE_NONE_USER=true

# Start Minikube
sudo minikube start --vm-driver=none --kubernetes-version=v1.9.0

# Fix the kubectl context, as it's often stale.
minikube update-context

# Enable ingress in minikube
sudo minikube addons enable ingress

printf "Waiting for kubernetes to start..."

# Wait for Kubernetes to be up and ready.
JSONPATH='{range .items[*]}{@.metadata.name}:{range @.status.conditions[*]}{@.type}={@.status};{end}{end}'
until kubectl get nodes -o jsonpath="$JSONPATH" 2>&1 | grep -q "Ready=True"; do
    sleep 1;
done

printf "done.\n"
