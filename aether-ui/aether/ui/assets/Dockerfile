FROM node:lts-slim

RUN apt-get update -qq && \
    apt-get -qq \
        --yes \
        --allow-downgrades \
        --allow-remove-essential \
        --allow-change-held-packages \
        install git mercurial

WORKDIR /code/

COPY ./package.json /code/package.json
RUN npm install -q -g npm && npm install -q

COPY ./ /code

RUN apt-get autoremove && apt-get clean

ENTRYPOINT ["/code/conf/entrypoint.sh"]
