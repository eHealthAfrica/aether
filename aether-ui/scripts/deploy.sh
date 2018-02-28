#!/usr/bin/env bash
set -e

export AWS_DEFAULT_REGION="eu-west-1"
COMMIT="${TRAVIS_COMMIT}"
BRANCH="${TRAVIS_BRANCH}"
IMAGE_REPO="387526361725.dkr.ecr.eu-west-1.amazonaws.com"

if [ "${BRANCH}" == "gather-on-aether" ]; then
  export APP=( gather )
  export ENV="dev"
fi

$(aws ecr get-login --region="${AWS_DEFAULT_REGION}" --no-include-email)

TOKEN="deploy_token_${ENV}"

function install_kubectl {
  curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl
  chmod +x ./kubectl
  sudo mv ./kubectl /usr/local/bin/kubectl
  mkdir -p ~/.kube
  openssl aes-256-cbc -K $encrypted_176cb6ce0b2f_key -iv $encrypted_176cb6ce0b2f_iv \
  -in conf/${ENV}_kube_config.enc -out ~/.kube/config -d
}

# authenticate to the K8's cluster
function configure_kubectl {
  install_kubectl
  kubectl proxy --port=8080 &
}

GATHER2_APP="gather-on-aether"
docker-compose build $APP

echo "Building Docker image ${IMAGE_REPO}/${GATHER2_APP}-${ENV}:${BRANCH}"
docker tag $APP "${IMAGE_REPO}/${GATHER2_APP}-${ENV}:${BRANCH}"
docker tag $APP "${IMAGE_REPO}/${GATHER2_APP}-${ENV}:${COMMIT}"
docker tag $APP "${IMAGE_REPO}/${GATHER2_APP}-${ENV}:latest"

echo "Pushing Docker image ${IMAGE_REPO}/${GATHER2_APP}-${ENV}:${BRANCH}"
docker push "${IMAGE_REPO}/${GATHER2_APP}-${ENV}:${BRANCH}"
docker push "${IMAGE_REPO}/${GATHER2_APP}-${ENV}:${COMMIT}"
docker push "${IMAGE_REPO}/${GATHER2_APP}-${ENV}:latest"
echo "Configure Kubectl"
configure_kubectl

echo "Deploying ${APP} to ${ENV}"
kubectl set image deployment/gather ${APP}=${IMAGE_REPO}/${GATHER2_APP}-${ENV}:${COMMIT}
kubectl rollout status deployment/${APP}
