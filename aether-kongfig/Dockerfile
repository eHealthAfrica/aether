FROM node:8-slim

COPY ./config.yml /config.yml

ARG KONG_CONSUMER

ARG KONG_APIKEY

ARG PROJECT_API_URL

RUN sed -i 's/KONG_CONSUMER/'"$KONG_CONSUMER"'/g' /config.yml

RUN sed -i 's/KONG_APIKEY/'"$KONG_APIKEY"'/g' /config.yml

RUN sed -i 's/PROJECT_API_URL/'"$PROJECT_API_URL"'/g' /config.yml

WORKDIR /config

ENV BETWEEN_CHECK_DELAY=2 \
    POST_START_DELAY=0 \
    CHECK_ATTEMPTS=60 \
    CONFIG= \
    DEBUG=false

COPY ./entrypoint.sh /usr/local/bin/entrypoint

RUN npm install kongfig -g --loglevel error

RUN chmod a+x /usr/local/bin/entrypoint

ENTRYPOINT ["entrypoint"]