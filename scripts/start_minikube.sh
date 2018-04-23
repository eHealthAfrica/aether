export CHANGE_MINIKUBE_NONE_USER=true

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

# Download kubectl, which is a requirement for using minikube.
curl -Lo kubectl https://storage.googleapis.com/kubernetes-release/release/v1.9.0/bin/linux/amd64/kubectl && chmod +x kubectl && sudo mv kubectl /usr/local/bin/

# Download minikube.
curl -lo minikube https://storage.googleapis.com/minikube/releases/v0.25.2/minikube-linux-amd64 && chmod +x minikube && sudo mv minikube /usr/local/bin/

# Start Minikube
sudo minikube start --vm-driver=none --kubernetes-version=v1.9.0

# Fix the kubectl context, as it's often stale.
minikube update-context

# Enable ingress in minikube
sudo minikube addons enable ingress

# Wait for Kubernetes to be up and ready.
JSONPATH='{range .items[*]}{@.metadata.name}:{range @.status.conditions[*]}{@.type}={@.status};{end}{end}'; until kubectl get nodes -o jsonpath="$JSONPATH" 2>&1 | grep -q "Ready=True"; do sleep 1; done

# Install helm
curl https://raw.githubusercontent.com/kubernetes/helm/master/scripts/get | bash

# Start helm
helm init

# Wait for the tiller deploy pod to be ready
kubectl rollout status -w deployment/tiller-deploy --namespace=kube-system
