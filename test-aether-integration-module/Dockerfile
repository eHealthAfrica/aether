FROM python:3.6-slim-jessie

################################################################################
## install app
################################################################################

WORKDIR /code
COPY ./ /code

RUN useradd -ms /bin/false aether && \
    chown -R aether: /code && \
    apt-get update -qq && \
    apt-get -qq --yes --force-yes install gcc && \
    pip install -q --upgrade pip && \
    pip install -q -f /code/conf/pip/dependencies -r /code/conf/pip/requirements.txt

ENTRYPOINT ["/code/entrypoint.sh"]
