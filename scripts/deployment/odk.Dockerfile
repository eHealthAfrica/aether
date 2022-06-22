################################################################################
## using alpine image to build version and revision files
################################################################################

FROM alpine AS app_resource

WORKDIR /tmp
COPY ./.git /tmp/.git
COPY ./scripts/deployment/setup_revision.sh /tmp/setup_revision.sh
RUN /tmp/setup_revision.sh


################################################################################
## using python image to build app
################################################################################

FROM python:3.8-slim

LABEL description="Aether ODK Module" \
      name="aether-odk" \
      author="eHealth Africa"

## set up container
WORKDIR /code
ENTRYPOINT ["/code/entrypoint.sh"]

COPY ./aether-odk-module/conf/docker/* /tmp/
RUN /tmp/setup.sh

## copy source code
COPY --chown=aether:aether ./aether-odk-module/ /code

## install dependencies
ENV VIRTUAL_ENV=/var/run/aether/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN mkdir -p $VIRTUAL_ENV && \
    python3 -m venv $VIRTUAL_ENV && \
    pip install -q --upgrade pip && \
    pip install -q -r /code/conf/pip/requirements.txt

## copy application version and revision
COPY --from=app_resource --chown=aether:aether /tmp/resources/. /var/tmp/
