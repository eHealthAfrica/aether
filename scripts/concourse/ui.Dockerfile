################################################################################
## using alpine image to build version and revision files
################################################################################

FROM alpine AS app_resource

WORKDIR /tmp
COPY ./.git /tmp/.git
COPY ./scripts/concourse/setup_revision.sh /tmp/setup_revision.sh
RUN /tmp/setup_revision.sh


################################################################################
## using node image to build react app
################################################################################

FROM node:lts-slim AS app_node

################################################################################
## setup container
################################################################################

WORKDIR /code/

COPY ./aether-ui/aether/ui/assets/ /code/
RUN npm install -q -g npm && npm install -q

################################################################################
## copy application version and git revision
################################################################################

COPY --from=app_resource /tmp/resources/. /var/tmp/

################################################################################
## build react app
################################################################################

RUN npm run build


################################################################################
## using python image to build app
################################################################################

FROM python:3.7-slim-buster AS app

LABEL description="Aether Kernel UI" \
      name="aether-ui" \
      author="eHealth Africa"

################################################################################
## setup container
################################################################################

WORKDIR /code

COPY ./aether-ui/conf/docker/* /tmp/
RUN /tmp/setup.sh

################################################################################
## install app
################################################################################

COPY ./aether-ui/ /code
RUN pip install -q --upgrade pip && \
    pip install -q -r /code/conf/pip/requirements.txt

################################################################################
## copy react app
################################################################################
COPY --from=app_node /code/bundles/. /code/aether/ui/assets/bundles

################################################################################
## copy application version and git revision
################################################################################

COPY --from=app_resource /tmp/resources/. /var/tmp/

################################################################################
## last setup steps
################################################################################

RUN chown -R aether: /code

ENTRYPOINT ["/code/entrypoint.sh"]
