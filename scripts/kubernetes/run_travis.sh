#!/usr/bin/env bash

./scripts/kubernetes/install_minikube.sh
./scripts/kubernetes/install_helm.sh
./scripts/kubernetes/start_minikube.sh
./scripts/kubernetes/start_helm.sh
./scripts/kubernetes/start_test_cluster.sh
./scripts/kubernetes/run_tests.sh test_all
