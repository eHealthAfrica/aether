#!/usr/bin/env bash
set -Eeuo pipefail

IMAGE_REPO='ehealthafrica'
APPS=( kernel odk couchdb-sync )
VERSION=`cat VERSION`

if [ -z "$TRAVIS_TAG" ];
then
  VERSION=${VERSION}-rc
fi

for APP in "${APPS[@]}"
do
  AETHER_APP="aether-${APP}"
	echo "version: $VERSION"
  echo "Building Docker image ${IMAGE_REPO}/${AETHER_APP}:${VERSION}"
  docker-compose build --build-arg GIT_REVISION=$TRAVIS_COMMIT \
  --build-arg VERSION=$VERSION $APP
  docker tag ${AETHER_APP} "${IMAGE_REPO}/${AETHER_APP}:${VERSION}"
  docker tag ${AETHER_APP} "${IMAGE_REPO}/${AETHER_APP}:latest"
  echo "Pushing Docker image ${IMAGE_REPO}/${AETHER_APP}:${VERSION}"
  docker push "${IMAGE_REPO}/${AETHER_APP}:${VERSION}"
  docker push "${IMAGE_REPO}/${AETHER_APP}:latest"
done
