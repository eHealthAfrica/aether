FROM python:3.6-slim-jessie

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
## copy application version and create git revision
################################################################################

ARG VERSION
RUN echo $VERSION > VERSION
ARG GIT_REVISION
RUN echo $GIT_REVISION > REVISION

ENTRYPOINT ["/code/entrypoint.sh"]
