# Developing locally with Minikube

This document outlines how to set up a local kubernetes cluster using [minikube](https://github.com/kubernetes/minikube) and [helm](https://helm.sh/).

## Setup

### Dependencies
- minikube ([installation instructions](https://kubernetes.io/docs/tasks/tools/install-minikube/))
- helm ([installation instructions](https://github.com/kubernetes/helm/blob/master/docs/install.md))

### Installation
If you are using ubuntu, you can probably make use of the installation process we use for Travis CI.

To install minikube on ubuntu, run:
```bash
sudo ./scripts/kubernetes/install_minikube.sh
```

To install helm on ubuntu, run:
```bash
sudo ./scripts/kubernetes/install_helm.sh --version v2.8.1
```

## Running a local kubernetes cluster

### Secrets

For local development with Kubernetes and Minikube, we need to create some secrets:
```bash
POSTGRES_PASSWORD=<postgres-password> ./scripts/generate-kubernetes-credentials.sh > helm/test-secrets.yaml
POSTGRES_PASSWORD=<postgres-password> ./scripts/kubernetes/install_secrets.sh && ./scripts/kubernetes/start_cluster.sh ./helm/overrides/local
```

### Accessing the aether APIs from the host
The ingress resources in the aether modules use hostnames to direct incoming traffic. In order to be able to access the aether APIs from a browser or a command line client on the host machine, we need to add a couple of entries to our `/etc/hosts` file.

To get a list of the exposed endpoints, run:
```bash
kubectl get ingress
```

The result should look similar to this:
```
NAME      HOSTS                 ADDRESS          PORTS     AGE
kernel    kernel.aether.local   192.168.99.100   80, 443   28m
odk       odk.aether.local      192.168.99.100   80, 443   28m
```

For each entry, add the address and the hostname at the bottom of your `/etc/hosts` file:
```
192.168.99.100 kernel.aether.local
192.168.99.100 odk.aether.local
```

## Running the tests
If you already have kernel and odk running, do:
```bash
./scripts/kubernetes/run_tests.sh test_all
```

To test a single module, use `./run_tests.sh test_<module-name>`. For example:
```bash
./scripts/kubernetes/run_tests.sh test_kernel
./scripts/kubernetes/run_tests.sh test_odk
```

To delete everything in the cluster, bring it back up and then run the tests, do:
```bash
./scripts/kubernetes/delete_all.sh && \
    ./scripts/kubernetes/install_secrets.sh && \
    ./scripts/kubernetes/start_cluster.sh ./helm/overrides/local && \
    ./scripts/kubernetes/run_tests.sh test_all
```
