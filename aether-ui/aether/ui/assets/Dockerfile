FROM node:lts-alpine

WORKDIR /code/
ENTRYPOINT ["/code/assets/conf/entrypoint.sh"]

ARG VERSION=0.0.0
ARG GIT_REVISION

RUN mkdir -p /var/tmp && \
    echo $VERSION > /var/tmp/VERSION && \
    echo $GIT_REVISION > /var/tmp/REVISION

COPY ./package.json /code/package.json
RUN npm install -q -g npm && npm install -q
ENV PATH /code/node_modules/.bin:$PATH

WORKDIR /code/assets
COPY ./ /code/assets

USER node
