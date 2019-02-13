FROM python:3.7-slim-stretch

################################################################################
## setup container
################################################################################

RUN apt-get update -qq \
    && apt-get -qq --yes --force-yes install gcc \
    && pip install --upgrade pip

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
## last setup steps
################################################################################

# create user to run container (avoid root user)
RUN useradd -ms /bin/false aether
RUN chown -R aether: /code

ENTRYPOINT ["/code/entrypoint.sh"]
