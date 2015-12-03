FROM ubuntu:14.04

RUN apt-get install -y wget
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main 9.4" > /etc/apt/sources.list.d/pgdg.list

RUN apt-get update && apt-get -y upgrade && apt-get install -y \
  git \
  python3-dev \
  python3-pip \
  postgresql-client-9.4 \
  postgresql-server-dev-9.4 \
  python-pypy.sandbox \
  npm

RUN pip3 install virtualenv uwsgi

RUN virtualenv ~/env/

ADD requirements.txt /code/gather2-core/requirements.txt
RUN ~/env/bin/pip install -r /code/gather2-core/requirements.txt

ADD . /code/
RUN ~/env/bin/python /code/manage.py collectstatic --no-input

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
