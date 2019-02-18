FROM node:dubnium-slim

RUN apt-get update -qq && apt-get -qq --yes --force-yes install git mercurial

WORKDIR /code/

COPY ./package.json /code/package.json
RUN npm install -q -g npm && npm install -q

COPY ./ /code

RUN apt-get autoremove && apt-get clean

ENTRYPOINT ["/code/conf/entrypoint.sh"]
