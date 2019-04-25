FROM python:3.7-slim-stretch

################################################################################
## install app
################################################################################

WORKDIR /code
COPY ./ /code

RUN pip install -q --upgrade pip && \
    pip install flake8 flake8-quotes

################################################################################
## copy application version and create git revision
################################################################################

ARG VERSION

RUN mkdir -p /var/tmp && \
    echo $VERSION > /var/tmp/VERSION

################################################################################
## last setup steps
################################################################################

ENTRYPOINT ["/code/build.sh"]
