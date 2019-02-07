FROM python:3.7-slim-stretch

################################################################################
## setup container
################################################################################

RUN apt-get update -qq \
    && apt-get -qq --yes --force-yes install gcc \
    && pip install -q --upgrade pip

################################################################################
## install app
## copy files one by one and split commands to use docker cache
################################################################################

WORKDIR /code

# This avoids reinstalling Python packages each time the image is rebuilt.
COPY ./requirements.txt /code/requirements.txt
RUN pip install -q -r requirements.txt

COPY . /code

ENTRYPOINT ["/code/entrypoint.sh"]
