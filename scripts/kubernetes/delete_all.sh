#!/usr/bin/env bash

# Delete all helm releases.
helm del --purge db
helm del --purge kernel
helm del --purge odk

# Delete all secrets and persistent volumes.
kubectl delete --all secrets
kubectl delete --all persistentvolumeclaims
kubectl delete --all persistentvolumes
