FROM python:3.7-slim-stretch

################################################################################
## setup container
################################################################################

COPY ./conf/docker/* /tmp/
RUN /tmp/setup.sh

################################################################################
## install app
## copy files one by one and split commands to use docker cache
################################################################################

WORKDIR /code

COPY ./conf/pip /code/conf/pip
RUN pip install -q --upgrade pip && \
    pip install -q -r /code/conf/pip/requirements.txt

COPY ./ /code

################################################################################
## copy application version and create git revision
################################################################################

ARG VERSION
ARG GIT_REVISION

RUN mkdir -p /var/tmp && \
    echo $VERSION > /var/tmp/VERSION && \
    echo $GIT_REVISION > /var/tmp/REVISION

################################################################################
## last setup steps
################################################################################

RUN chown -R aether: /code

ENTRYPOINT ["/code/entrypoint.sh"]
