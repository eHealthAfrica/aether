FROM python:3.6

################################################################################
## setup container
################################################################################

COPY conf/docker/* /tmp/
RUN /tmp/setup.sh


################################################################################
## install app
## copy files one by one and split commands to use docker cache
################################################################################

WORKDIR /code

COPY ./conf/pip /code/conf/pip
RUN pip install -r /code/conf/pip/requirements.txt

COPY ./ /code

ENTRYPOINT ["/code/entrypoint.sh"]
