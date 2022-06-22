################################################################################
## using alpine image to build version and revision files
################################################################################

FROM alpine AS app_resource

WORKDIR /tmp
COPY ./.git /tmp/.git
COPY ./scripts/deployment/setup_revision.sh /tmp/setup_revision.sh
RUN /tmp/setup_revision.sh


################################################################################
## using node image to build react app
################################################################################

FROM node:14-alpine AS app_node

## set up container
WORKDIR /assets/
## copy application version and git revision
COPY --from=app_resource /tmp/resources/. /var/tmp/
## copy source code
COPY ./aether-ui/aether/ui/assets/ /assets/
## build react app
RUN npm install -s --no-audit --no-fund --no-package-lock && \
    npm run build


################################################################################
## using python image to build app
################################################################################

FROM python:3.8-slim AS app

LABEL description="Aether Kernel UI" \
      name="aether-ui" \
      author="eHealth Africa"

## set up container
WORKDIR /code
ENTRYPOINT ["/code/entrypoint.sh"]

COPY ./aether-ui/conf/docker/* /tmp/
RUN /tmp/setup.sh

## copy source code
COPY --chown=aether:aether ./aether-ui/ /code

## install dependencies
ENV VIRTUAL_ENV=/var/run/aether/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN mkdir -p $VIRTUAL_ENV && \
    python3 -m venv $VIRTUAL_ENV && \
    pip install -q --upgrade pip && \
    pip install -q -r /code/conf/pip/requirements.txt

## copy react app
RUN rm -Rf /code/aether/ui/assets/
COPY --from=app_node --chown=aether:aether /assets/bundles/. /code/aether/ui/assets/bundles

## copy application version and revision
COPY --from=app_resource --chown=aether:aether /tmp/resources/. /var/tmp/
