FROM node:dubnium-slim

WORKDIR /code/

COPY ./package.json /code/package.json
RUN npm install -q -g npm && npm install -q

COPY ./ /code

ENTRYPOINT ["/code/conf/entrypoint.sh"]
