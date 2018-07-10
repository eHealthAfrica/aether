# Developing locally with Minikube

We are in the process of switching from docker-compose to kubernetes for local development. This document outlines how to set up a local kubernetes cluster using [minikube](https://github.com/kubernetes/minikube) and [helm](https://helm.sh/).

## Setup

### Dependencies
- minikube ([installation instructions](https://kubernetes.io/docs/tasks/tools/install-minikube/))
- helm ([installation instructions](https://github.com/kubernetes/helm/blob/master/docs/install.md))

### Installation
If you are using ubuntu, you can probably make use of the installation process we use for Travis CI.

To install minikube on ubuntu, run:
```
sudo ./scripts/kubernetes/install_minikube.sh
```
To install helm on ubuntu, run:
```
sudo ./scripts/kubernetes/install_helm.sh --version v2.8.1
```

## Running a local kubernetes cluster

### Secrets

For local development with Kubernetes and Minikube, we need to create some secrets.

```bash
POSTGRES_PASSWORD=<postgres-password> ./scripts/generate-kubernetes-credentials.sh > helm/test-secrets.yaml
```

The file `helm/test-secrets.yaml` will get picked up by `./scripts/install_secrets.sh` (see below).

### Environments
To start the `kernel` and `odk` modules in a local minikube cluster with code reloading enabled, we need to mount our aether repository in minikube:

```
minikube mount `pwd`:/aether
```
This process needs to keep running in order for our mount to work, so start it in a separate terminal tab or background it in your current one.

Once the mount process is running, we can do:
```
POSTGRES_PASSWORD=<postgres-password> ./scripts/kubernetes/install_secrets.sh && ./scripts/kubernetes/start_cluster.sh ./helm/overrides/local
```

This will bring up both applications with auto-reloading of django code enabled.

### Accessing the aether APIs from the host

The ingress resources in the aether modules use hostnames to direct incoming traffic. In order to be able to access the aether APIs from a browser or a command line client on the host machine, we need to add a couple of entries to our `/etc/hosts` file.

To get a list of the exposed endpoints, run:
```
kubectl get ingress
```
The result should look similar to this:
```
NAME      HOSTS                 ADDRESS          PORTS     AGE
kernel    kernel.aether.local   192.168.99.100   80, 443   28m
odk       odk.aether.local      192.168.99.100   80, 443   28m
```
For each entry, add the address and the hostname to your `/etc/hosts` file:
```
# /etc/hosts
...
192.168.99.100 kernel.aether.local
192.168.99.100 odk.aether.local
...
```

## Running the tests
If you already have kernel and odk running, do:
```
./scripts/kubernetes/run_tests.sh test_all
```
To test a single module, use `./run_tests.sh test_<module-name>`. For example:
```
./scripts/kubernetes/run_tests.sh test_kernel
./scripts/kubernetes/run_tests.sh test_odk
```
To delete everything in the cluster, bring it back up and then run the tests, do:
```
./scripts/kubernetes/delete_all.sh && \
    ./scripts/kubernetes/install_secrets.sh && \
    ./scripts/kubernetes/start_cluster.sh ./helm/overrides/local && \
    ./scripts/kubernetes/run_tests.sh test_all
```
