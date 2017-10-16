#!/usr/bin/env bash
set -e

export PREFIX=""
export APPS=( core couchdb-sync odk-importer )

COMMIT="${TRAVIS_COMMIT}"
BRANCH="${TRAVIS_BRANCH}"
export AWS_DEFAULT_REGION="eu-west-1"
IMAGE_REPO="387526361725.dkr.ecr.eu-west-1.amazonaws.com"

if [ "${BRANCH}" == "develop" ]; then
  export ENV="dev"
  export PREFIX="gather2"
  export CLUSTER_NAME="ehealth-africa"
elif [ "${BRANCH}" == "master" ]; then
  echo "commit on master, setting ENV to production"
  export ENV="prod"
  export PREFIX="grid"
  export CLUSTER_NAME="ehealth-africa"
fi

$(aws ecr get-login --region="${AWS_DEFAULT_REGION}")
for APP in "${APPS[@]}"
do
  GATHER2_APP="${PREFIX}-${APP}"
  docker-compose build $APP
  echo "Building Docker image ${IMAGE_REPO}/${GATHER2_APP}-${ENV}:${BRANCH}"
  docker tag $APP "${IMAGE_REPO}/${GATHER2_APP}-${ENV}:${BRANCH}"
  docker tag $APP "${IMAGE_REPO}/${GATHER2_APP}-${ENV}:${COMMIT}"
  echo "Pushing Docker image ${IMAGE_REPO}/${GATHER2_APP}-${ENV}:${BRANCH}"
  docker push "${IMAGE_REPO}/${GATHER2_APP}-${ENV}:${BRANCH}"
  docker push "${IMAGE_REPO}/${GATHER2_APP}-${ENV}:${COMMIT}"
  echo "Deploying ${APP} to ${ENV}"
  ecs deploy --timeout 600 $CLUSTER_NAME-$ENV $GATHER2_APP -i $APP "${IMAGE_REPO}/${GATHER2_APP}-${ENV}:${COMMIT}"
done
