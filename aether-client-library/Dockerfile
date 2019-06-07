FROM python:3.7-slim-stretch

ARG VERSION

WORKDIR /code
COPY ./ /code

RUN pip install -q --upgrade pip && \
    pip install -q -r /code/conf/pip/requirements.txt && \
    mkdir -p /var/tmp && \
    echo $VERSION > /var/tmp/VERSION

ENTRYPOINT ["/code/entrypoint.sh"]
