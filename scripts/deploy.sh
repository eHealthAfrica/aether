#!/usr/bin/env bash
set -e

COMMIT="${TRAVIS_COMMIT}"
BRANCH="${TRAVIS_BRANCH}"
export AWS_DEFAULT_REGION="eu-west-1"
IMAGE_REPO="387526361725.dkr.ecr.eu-west-1.amazonaws.com"

if [ "${BRANCH}" == "develop" ]; then
  export ENV="dev"
  export PREFIX="aether"
  export APPS=( kernel odk )
  export CLUSTER_NAME="ehealth-africa"
fi

$(aws ecr get-login --region="${AWS_DEFAULT_REGION}" --no-include-email)
for PREFIX in "${PREFIX[@]}"
do
  for APP in "${APPS[@]}"
  do
    AETHER_APP="${PREFIX}-${APP}"
    docker-compose build $APP
    # build nginx containers
    docker-compose -f docker-compose-nginx.yml build $APP-nginx 
    docker tag "${AETHER_APP}-nginx" "${IMAGE_REPO}/${AETHER_APP}-nginx-${ENV}:latest"
    docker push "${IMAGE_REPO}/${AETHER_APP}-nginx-${ENV}:latest"

    echo "Building Docker image ${IMAGE_REPO}/${AETHER_APP}-${ENV}:${BRANCH}"
    docker-compose build $APP
    docker tag aether-$APP "${IMAGE_REPO}/${AETHER_APP}-${ENV}:${BRANCH}"
    docker tag aether-$APP "${IMAGE_REPO}/${AETHER_APP}-${ENV}:${COMMIT}"
    echo "Pushing Docker image ${IMAGE_REPO}/${AETHER_APP}-${ENV}:${BRANCH}"
    docker push "${IMAGE_REPO}/${AETHER_APP}-${ENV}:${BRANCH}"
    docker push "${IMAGE_REPO}/${AETHER_APP}-${ENV}:${COMMIT}"
    echo "Deploying ${APP} to ${ENV}"
    ecs deploy --timeout 600 $CLUSTER_NAME-$ENV $AETHER_APP -i $APP "${IMAGE_REPO}/${AETHER_APP}-${ENV}:${COMMIT}"
  done
done
