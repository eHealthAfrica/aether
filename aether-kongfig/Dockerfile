FROM node:5-slim

WORKDIR /config

ENV BETWEEN_CHECK_DELAY=2 \
    POST_START_DELAY=0 \
    CHECK_ATTEMPTS=60 \
    CONFIG= \
    DEBUG=false

COPY ./entrypoint.sh /usr/local/bin/entrypoint

RUN npm install kongfig -g ; chmod a+x /usr/local/bin/entrypoint

ENTRYPOINT ["entrypoint"]