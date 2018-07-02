FROM python:3.6

################################################################################
## setup container
################################################################################

################################################################################
## install app
## copy files one by one and split commands to use docker cache
################################################################################

WORKDIR /code

COPY ./conf/pip /code/conf/pip

RUN pip3 install -f /code/conf/pip/dependencies -r /code/conf/pip/requirements.txt

COPY ./ /code

################################################################################
## last setup steps
################################################################################

# create user to run container (avoid root user)
RUN useradd -ms /bin/false aether
RUN chown -R aether: /code

ENTRYPOINT ["/code/entrypoint.sh"]
