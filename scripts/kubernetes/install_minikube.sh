#!/usr/bin/env bash

install_bin() {
    local exe=${1:?}
    test -n "${TRAVIS}" && sudo install -v ${exe} /usr/local/bin || install ${exe} ${GOPATH:?}/bin
}

check_or_build_nsenter() {
    which nsenter >/dev/null && return 0
    echo "INFO: Getting 'nsenter' ..."
    curl -LO http://mirrors.kernel.org/ubuntu/pool/main/u/util-linux/util-linux_2.30.1-0ubuntu4_amd64.deb
    dpkg -x ./util-linux_2.30.1-0ubuntu4_amd64.deb /tmp/out
    install_bin /tmp/out/usr/bin/nsenter
}

# `nsenter` might not be installed but minikube needs it. `install_bin` and `check_or_build_nsenter` were lifted from https://github.com/kubeless/kubeless/blob/master/script/cluster-up-minikube.sh
check_or_build_nsenter

# Download kubectl, which is a requirement for using minikube
curl -Lo kubectl https://storage.googleapis.com/kubernetes-release/release/v1.9.0/bin/linux/amd64/kubectl && chmod +x kubectl && sudo mv kubectl /usr/local/bin/

# Download minikube
curl -lo minikube https://storage.googleapis.com/minikube/releases/v0.25.2/minikube-linux-amd64 && chmod +x minikube && sudo mv minikube /usr/local/bin/
