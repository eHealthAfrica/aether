FROM python:3.8-slim-buster

LABEL description="Aether Entity Extraction Module" \
      name="aether-extractor" \
      author="eHealth Africa"

################################################################################
## set up container
################################################################################

RUN apt-get update -qq && \
    apt-get -qq \
        --yes \
        --allow-downgrades \
        --allow-remove-essential \
        --allow-change-held-packages \
        install gcc redis-server curl && \
    useradd -ms /bin/false aether

WORKDIR /code
ENTRYPOINT ["/code/entrypoint.sh"]

################################################################################
## install dependencies
## copy files one by one and split commands to use docker cache
################################################################################

COPY --chown=aether:aether ./conf/pip /code/conf/pip
RUN pip install -q --upgrade pip && \
    pip install -q -r /code/conf/pip/requirements.txt
COPY --chown=aether:aether ./ /code

################################################################################
## create application version and revision files
################################################################################

ARG VERSION=0.0.0
ARG GIT_REVISION

RUN mkdir -p /var/tmp && \
    echo $VERSION > /var/tmp/VERSION && \
    echo $GIT_REVISION > /var/tmp/REVISION
