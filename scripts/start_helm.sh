#!/bin/bash

# Start helm
helm init

# Wait for the tiller deploy pod to be ready
kubectl rollout status -w deployment/tiller-deploy --namespace=kube-system
