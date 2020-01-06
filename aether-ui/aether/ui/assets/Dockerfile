FROM node:lts-slim

ARG VERSION=0.0.0
ARG GIT_REVISION

RUN mkdir -p /var/tmp && \
    echo $VERSION > /var/tmp/VERSION && \
    echo $GIT_REVISION > /var/tmp/REVISION

WORKDIR /code/

COPY ./package.json /code/package.json
RUN npm install -q -g npm && npm install -q

COPY ./ /code

RUN apt-get autoremove && apt-get clean

ENTRYPOINT ["/code/conf/entrypoint.sh"]
