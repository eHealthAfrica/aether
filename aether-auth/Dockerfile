FROM python:3.6-slim-jessie

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

# This avoids reinstalling Python packages each time the image is rebuilt.
ADD ./requirements.txt /code/requirements.txt

RUN pip install -r requirements.txt

COPY . /code

ENTRYPOINT ["/code/entrypoint.sh"]
