#!/usr/bin/env bash
set -e

export APPS=( gather2-core gather2-couchdb-sync gather2-odk-importer )

if [ "${TRAVIS_BRANCH}" == "develop" ]; then
  export ENV="dev"
fi

TAG="${TRAVIS_TAG}"
COMMIT="${TRAVIS_COMMIT}"
BRANCH="${TRAVIS_BRANCH}"
PR="${TRAVIS_PULL_REQUEST}"
export AWS_DEFAULT_REGION="eu-west-1"
IMAGE_REPO="387526361725.dkr.ecr.eu-west-1.amazonaws.com"

if ! [ -n "${TAG}" ]; then
  echo "Not a git tag, tagging as: ${COMMIT}"
  TAG="${COMMIT}"
fi
export TAG

$(aws ecr get-login --region="${AWS_DEFAULT_REGION}")
for APP in "${APPS[@]}"
do
  cd $APP
  echo "Building Docker image ${IMAGE_REPO}/${APP}-${ENV}:${TAG}"
  docker build -t "${IMAGE_REPO}/${APP}-${ENV}:${TAG}" .
  docker build -t "${IMAGE_REPO}/${APP}-${ENV}:${BRANCH}" .
  echo "Pushing Docker image ${IMAGE_REPO}/${APP}-${ENV}:${TAG}"
  docker push "${IMAGE_REPO}/${APP}-${ENV}:${TAG}"
  docker push "${IMAGE_REPO}/${APP}-${ENV}:${BRANCH}"
  echo "Deploying ${APP}"
  ecs deploy --timeout 600 "gather2-${ENV}" $APP -i $APP "${IMAGE_REPO}/${APP}-${ENV}:${TAG}"
  cd ../
done
