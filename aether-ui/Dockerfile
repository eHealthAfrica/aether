################################################################################
## using node image to install node dependencies
################################################################################

FROM node:carbon AS ui_node


################################################################################
## setup container
################################################################################

# Upgrade npm to last version
RUN npm install -g npm

WORKDIR /code/


################################################################################
## React app
################################################################################

COPY ./package.json /code/package.json
RUN npm install --loglevel warn



################################################################################
## using python image to install django app
################################################################################

FROM python:3.6 AS ui_py


################################################################################
## setup container
################################################################################

## make node+npm available within the python container
COPY --from=ui_node /usr/local/bin/nodejs        /usr/local/bin/nodejs
COPY --from=ui_node /usr/local/lib/node_modules  /usr/local/lib/node_modules

COPY ./conf/docker/* /tmp/
RUN /tmp/setup.sh

WORKDIR /code/


################################################################################
## Django app
################################################################################

COPY ./conf/pip /code/conf/pip
RUN pip install -f /code/conf/pip/dependencies -r /code/conf/pip/requirements.txt


################################################################################
## last setup steps
################################################################################

COPY ./ /code

# create user to run container (avoid root user)
RUN useradd -ms /bin/false aether
RUN chown -R aether: /code

# move this line to the last to speed up setup
COPY --from=ui_node /code/node_modules /code/node_modules

ENTRYPOINT ["/code/entrypoint.sh"]
