#!/usr/bin/env bash
set -e

export APPS=( core couchdb-sync odk-importer )

COMMIT="${TRAVIS_COMMIT}"
BRANCH="${TRAVIS_BRANCH}"
export AWS_DEFAULT_REGION="eu-west-1"
IMAGE_REPO="387526361725.dkr.ecr.eu-west-1.amazonaws.com"

if [ "${BRANCH}" == "develop" ]; then
  export ENV="dev"
elif [ "${BRANCH}" == "master" ]; then
  echo "commit on master, setting ENV to production"
  export ENV="prod"
fi

$(aws ecr get-login --region="${AWS_DEFAULT_REGION}")
for APP in "${APPS[@]}"
do
  GATHER2_APP="gather2-${APP}"
  echo "Building Docker image ${IMAGE_REPO}/${GATHER2_APP}-${ENV}:${BRANCH}"
  docker tag $APP "${IMAGE_REPO}/${GATHER2_APP}-${ENV}:${BRANCH}"
  docker tag $APP "${IMAGE_REPO}/${GATHER2_APP}-${ENV}:${COMMIT}"
  echo "Pushing Docker image ${IMAGE_REPO}/${GATHER2_APP}-${ENV}:${BRANCH}"
  docker push "${IMAGE_REPO}/${GATHER2_APP}-${ENV}:${BRANCH}"
  docker push "${IMAGE_REPO}/${GATHER2_APP}-${ENV}:${COMMIT}"
  echo "Deploying ${APP} to ${ENV}"
  ecs deploy --timeout 600 "gather2-${ENV}" $GATHER2_APP -i $APP "${IMAGE_REPO}/${GATHER2_APP}-${ENV}:${COMMIT}"
done
