FROM python:3.6


################################################################################
## install app
## copy files one by one and split commands to use docker cache
################################################################################


WORKDIR /

COPY ./conf/pip /code/conf/pip
COPY ./ /code

WORKDIR /code

RUN pip install -f /code/conf/pip/dependencies -r /code/conf/pip/requirements.txt


################################################################################
## last setup steps
################################################################################

# create user to run container (avoid root user)
RUN useradd -ms /bin/false aether
RUN chown -R aether: /code

ENTRYPOINT ["/code/entrypoint.sh"]
