#!/usr/bin/env bash

./scripts/kubernetes/install_minikube.sh
./scripts/kubernetes/install_helm.sh
./scripts/kubernetes/start_minikube.sh
./scripts/kubernetes/start_helm.sh
kubectl create namespace test && kubectl config set-context $(kubectl config current-context) --namespace=test
./scripts/kubernetes/install_secrets.sh
./scripts/kubernetes/start_cluster.sh ./helm/overrides/test
./scripts/kubernetes/run_tests.sh test_all
