FROM python:3.7-slim-stretch

################################################################################
## install app
################################################################################

WORKDIR /code
COPY ./ /code

RUN useradd -ms /bin/false aether && \
    chown -R aether: /code && \
    pip install -q --upgrade pip && \
    pip install -q -r /code/conf/pip/requirements.txt

################################################################################
## copy application version
################################################################################

ARG VERSION
RUN mkdir -p /var/tmp && \
    echo $VERSION > /var/tmp/VERSION

################################################################################
## last setup steps
################################################################################

ENTRYPOINT ["/code/entrypoint.sh"]
