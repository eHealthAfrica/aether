#!/bin/bash
set -e
set -x

TAG=$TRAVIS_TAG
BRANCH=$TRAVIS_BRANCH
PR=$TRAVIS_PULL_REQUEST

echo $TAG
echo $BRANCH
echo $PR

if [ -z $TAG ]
then
    echo "No tags, tagging as: latest"
    TAG="latest"
fi

# if this is on the master branch and this is not a PR, deploy it
if [ $BRANCH = "master" -a $PR = "false" ]
then
    aws ecr get-login --region=us-east-1 | bash
    docker tag -f gather2_core:latest 387526361725.dkr.ecr.us-east-1.amazonaws.com/gather2core:$TAG
    docker push 387526361725.dkr.ecr.us-east-1.amazonaws.com/gather2core:$TAG

    fab stage preparedeploy

    # we never want our elastic beanstalk to use tag "latest" so if this is an
    # un-tagged build, use the commit hash
    if [ $TAG = "latest" ]
    then
        TAG=$TRAVIS_COMMIT
    fi
    eb deploy -l $TAG
fi
