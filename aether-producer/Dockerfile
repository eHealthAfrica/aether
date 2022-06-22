FROM python:3.8-slim

LABEL description="Aether Kafka Producer" \
      name="aether-producer" \
      author="eHealth Africa"

################################################################################
## set up container
################################################################################

RUN apt-get update -qq > /dev/null && \
    apt-get -qq \
        --yes \
        --allow-downgrades \
        --allow-remove-essential \
        --allow-change-held-packages \
        install gcc > /dev/null && \
    useradd -ms /bin/false aether

WORKDIR /code
ENTRYPOINT ["/code/entrypoint.sh"]

################################################################################
## install app
## copy files one by one and split commands to use docker cache
################################################################################

COPY --chown=aether:aether ./conf/pip /code/conf/pip

ENV VIRTUAL_ENV=/var/run/aether/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN mkdir -p $VIRTUAL_ENV && \
    python3 -m venv $VIRTUAL_ENV && \
    pip install -q --upgrade pip && \
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
