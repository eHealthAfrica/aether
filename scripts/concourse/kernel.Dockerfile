################################################################################
## using alpine image to build version and revision files
################################################################################

FROM alpine AS app_resource

WORKDIR /tmp
COPY ./.git /tmp/.git
COPY ./scripts/concourse/setup_revision.sh /tmp/setup_revision.sh
RUN /tmp/setup_revision.sh


################################################################################
## using python image to build app
################################################################################

FROM python:3.7-slim-buster

LABEL description="Aether Kernel" \
      name="aether-kernel" \
      author="eHealth Africa"

## set up container
WORKDIR /code
ENTRYPOINT ["/code/entrypoint.sh"]

COPY ./aether-kernel/conf/docker/* /tmp/
RUN /tmp/setup.sh

## copy source code
COPY --chown=aether:aether ./aether-kernel/ /code

## install dependencies
RUN pip install -q --upgrade pip && \
    pip install -q -r /code/conf/pip/requirements.txt

## copy application version and revision
COPY --from=app_resource --chown=aether:aether /tmp/resources/. /var/tmp/
