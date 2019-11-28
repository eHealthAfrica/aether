FROM python:3.7-slim-stretch

ARG VERSION

WORKDIR /code

COPY ./conf/pip /code/conf/pip

RUN apt-get update -qq && \
    apt-get -qq \
        --yes \
        --allow-downgrades \
        --allow-remove-essential \
        --allow-change-held-packages \
        install gcc libssl-dev && \
    pip install -q --upgrade pip && \
    pip install -q -r /code/conf/pip/requirements.txt && \
    mkdir -p /var/tmp && \
    echo $VERSION > /var/tmp/VERSION

COPY ./ /code

ENTRYPOINT ["/code/entrypoint.sh"]
