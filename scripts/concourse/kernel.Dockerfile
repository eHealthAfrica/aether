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

################################################################################
## setup container
################################################################################

WORKDIR /code
COPY ./aether-kernel/conf/docker/* /tmp/
RUN /tmp/setup.sh

################################################################################
## install app
################################################################################

COPY ./aether-kernel/ /code
RUN pip install -q --upgrade pip && \
    pip install -q -r /code/conf/pip/requirements.txt

################################################################################
## copy application version and git revision
################################################################################

COPY --from=app_resource /tmp/resources/. /var/tmp/

################################################################################
## last setup steps
################################################################################

RUN chown -R aether: /code

ENTRYPOINT ["/code/entrypoint.sh"]
