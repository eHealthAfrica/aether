FROM python:3.7-slim-stretch

################################################################################
## setup container
################################################################################

COPY ./conf/docker/* /tmp/
RUN /tmp/setup.sh

################################################################################
## install app
## copy files one by one and split commands to use docker cache
################################################################################

WORKDIR /code

COPY ./conf/pip /code/conf/pip
RUN pip install -q --upgrade pip && \
    pip install -q -f /code/conf/pip/dependencies -r /code/conf/pip/requirements.txt

COPY ./ /code

################################################################################
## copy application version and create git revision
################################################################################

ARG VERSION
RUN echo $VERSION > VERSION
ARG GIT_REVISION
RUN echo $GIT_REVISION > REVISION

################################################################################
## last setup steps
################################################################################

# create user to run container (avoid root user)
RUN useradd -ms /bin/false aether
RUN chown -R aether: /code

ENTRYPOINT ["/code/entrypoint.sh"]
