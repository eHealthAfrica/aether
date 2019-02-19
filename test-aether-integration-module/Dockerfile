FROM python:3.6-slim-jessie

################################################################################
## install app
################################################################################

WORKDIR /code
COPY ./ /code

RUN useradd -ms /bin/false aether && \
    chown -R aether: /code && \
    apt-get update -qq && \
    apt-get -qq --yes --allow-downgrades --allow-remove-essential --allow-change-held-packages install gcc && \
    pip install -q --upgrade pip && \
    pip install -q -f /code/conf/pip/dependencies -r /code/conf/pip/requirements.txt

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

ENTRYPOINT ["/code/entrypoint.sh"]
