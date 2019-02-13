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

ENTRYPOINT ["/code/entrypoint.sh"]
