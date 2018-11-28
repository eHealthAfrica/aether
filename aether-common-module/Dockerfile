FROM python:3.6-slim-jessie

################################################################################
## setup container
################################################################################

RUN pip install --upgrade pip

################################################################################
## install app
## copy files one by one and split commands to use docker cache
################################################################################

WORKDIR /code

COPY ./conf/pip/requirements.txt /code/conf/pip/requirements.txt

RUN pip install -q -r /code/conf/pip/requirements.txt

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
