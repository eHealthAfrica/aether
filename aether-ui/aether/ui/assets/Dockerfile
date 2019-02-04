FROM node:carbon-slim


################################################################################
## setup container
################################################################################

WORKDIR /code/

COPY ./package.json /code/package.json

# Upgrade npm to last version
RUN npm install -g npm
RUN npm install --loglevel warn


################################################################################
## Last steps
################################################################################

COPY ./ /code
ENTRYPOINT ["/code/conf/entrypoint.sh"]
