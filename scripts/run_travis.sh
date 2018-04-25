#!/bin/bash

./scripts/install_minikube.sh
./scripts/install_helm.sh
./scripts/start_minikube.sh
./scripts/start_helm.sh
./scripts/start_test_cluster.sh
./scripts/run_tests.sh test_all
