FROM python:3.7-slim-stretch

################################################################################
## setup container
################################################################################

RUN apt-get update -qq && \
    apt-get -qq \
        --yes \
        --allow-downgrades \
        --allow-remove-essential \
        --allow-change-held-packages \
        install gcc

################################################################################
## install app
## copy files one by one and split commands to use docker cache
################################################################################

WORKDIR /code

# This avoids reinstalling Python packages each time the image is rebuilt.
COPY ./requirements.txt /code/requirements.txt
RUN pip install -q --upgrade pip && \
    pip install -q -f /code/conf/pip/dependencies -r /code/conf/pip/requirements.txt

COPY . /code

ENTRYPOINT ["/code/entrypoint.sh"]
