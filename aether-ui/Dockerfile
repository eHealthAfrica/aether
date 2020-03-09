FROM python:3.7-slim-buster

LABEL description="Aether Kernel UI" \
      name="aether-ui" \
      author="eHealth Africa"

################################################################################
## set up container
################################################################################

COPY ./conf/docker/* /tmp/
RUN /tmp/setup.sh

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
