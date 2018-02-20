#!/usr/bin/env bash
set -e

VERSION=`cat VERSION`
IMAGE_REPO='ehealthafrica'

export APPS=( kernel odk )

for APP in "${APPS[@]}"
do
	VERSION=`cat $APP/VERSION`
	echo "version: $version"

	if git rev-parse -q --verify "refs/tags/$VERSION" >/dev/null; then
	    echo "Tag already exists..."
	    exit 0
	else
		echo "Tag does not exist, creating tag..."
		# tag the release 
		git tag -a "$VERSION" -m "version $VERSION"
		git push --tags

	  AETHER_APP="aether-${APP}"
	  echo "Building Docker image ${IMAGE_REPO}/${AETHER_APP}:${VERSION}"
	  docker-compose build --build-args GIT_REVISION=$TRAVIS_COMMIT $APP
	  docker tag aether-$APP "${IMAGE_REPO}/${AETHER_APP}:${VERSION}"
	  docker tag aether-$APP "${IMAGE_REPO}/${AETHER_APP}:latest"
	  echo "Pushing Docker image ${IMAGE_REPO}/${AETHER_APP}:${VERSION}"
	  docker push "${IMAGE_REPO}/${AETHER_APP}:${VERSION}"
	  docker push "${IMAGE_REPO}/${AETHER_APP}:latest"
	fi
done
