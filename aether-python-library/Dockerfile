FROM python:3.7-slim-stretch

ARG VERSION

RUN apt-get update -qq && \
    apt-get -qq \
        --yes \
        --allow-downgrades \
        --allow-remove-essential \
        --allow-change-held-packages \
        install gcc

WORKDIR /code
COPY ./ /code

RUN pip install -q --upgrade pip && \
    pip install -q -r /code/conf/pip/requirements.txt && \
    mkdir -p /var/tmp && \
    echo $VERSION > /var/tmp/VERSION

ENTRYPOINT ["/code/entrypoint.sh"]
