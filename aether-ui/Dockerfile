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

# create distributed app
COPY ./ /code
RUN npm run webpack


################################################################################
## using python image to install django app
################################################################################

FROM python:3.6 AS ui_py


################################################################################
## setup container
################################################################################

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

# copy distributed app into Django app
COPY --from=ui_node /code/aether/ui/assets/bundles /code/aether/ui/assets/bundles

# create user to run container (avoid root user)
RUN useradd -ms /bin/false aether
RUN chown -R aether: /code

ENTRYPOINT ["/code/entrypoint.sh"]
