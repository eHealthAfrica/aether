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

FROM python:3.8-slim-buster

LABEL description="Aether Entity Extraction Module" \
      name="aether-extractor" \
      author="eHealth Africa"

## set up container
WORKDIR /code
ENTRYPOINT ["/code/entrypoint.sh"]

RUN apt-get update -qq && \
    apt-get -qq \
        --yes \
        --allow-downgrades \
        --allow-remove-essential \
        --allow-change-held-packages \
        install gcc redis-server curl && \
    useradd -ms /bin/false aether

## copy source code
COPY --chown=aether:aether ./aether-entity-extraction-module/ /code

## install dependencies
RUN pip install -q --upgrade pip && \
    pip install -q -r /code/conf/pip/requirements.txt

## copy application version and revision
COPY --from=app_resource --chown=aether:aether /tmp/resources/. /var/tmp/
