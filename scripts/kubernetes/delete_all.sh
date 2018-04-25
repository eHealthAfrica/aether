#!/usr/bin/env bash

helm del --purge db
helm del --purge kernel
helm del --purge odk

kubectl delete --all pods
kubectl delete --all deployments
kubectl delete --all services
kubectl delete --all secrets
kubectl delete --all persistentvolumeclaims
kubectl delete --all persistentvolumes
