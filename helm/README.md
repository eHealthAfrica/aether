# Developing locally with Minikube

We are in the process of switching from docker-compose to kubernetes for local development. This document outlines how to set up a local kubernetes cluster using [minikube](https://github.com/kubernetes/minikube) and [helm](https://helm.sh/).

## Setup

### Dependencies
- minikube [Installation instructions](https://kubernetes.io/docs/tasks/tools/install-minikube/)
- helm [Installation instructions](https://github.com/kubernetes/helm/blob/master/docs/install.md)

### Installation
If you are using ubuntu, you can probably make use of the installation we use for Travis CI.

To install minikube on ubuntu, run:
```
./scripts/kubernetes/install_minikube.sh
```
To install helm on ubuntu, run:
```
./scripts/kubernetes/install_helm.sh
```

## Running a local kubernetes cluster

### Code reloading
mounting

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
For each entry copy, add the address and the hostname to your `/etc/hosts` file:
```
# /etc/hosts
...
192.168.99.100 kernel.aether.local
192.168.99.100 odk.aether.local
...
```

## Running the tests
