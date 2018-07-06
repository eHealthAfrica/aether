FROM node:carbon


################################################################################
## setup container
################################################################################

# Upgrade npm to last version
RUN npm install -g npm

WORKDIR /code/

COPY ./package.json /code/package.json
RUN npm install --loglevel warn


################################################################################
## Last steps
################################################################################

COPY ./ /code
ENTRYPOINT ["/code/conf/entrypoint.sh"]
