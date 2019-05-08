FROM python:3.7-slim-stretch

ARG VERSION
WORKDIR /code
COPY ./ /code

RUN pip install -q --upgrade pip && \
    pip install flake8 flake8-quotes && \
    mkdir -p /var/tmp && \
    echo $VERSION > /var/tmp/VERSION

ENTRYPOINT ["/code/build.sh"]
