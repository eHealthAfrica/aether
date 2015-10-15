FROM ubuntu:14.04

RUN apt-get install -y wget
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc |  apt-key add -
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main 9.5" > /etc/apt/sources.list.d/pgdg.list
RUN apt-get --purge remove postgresql\*

RUN apt-get update && apt-get -y upgrade && apt-get install -y \
  git \
  curl \
  python-dev \
  python3-dev \
  python-virtualenv \
  postgresql-client-9.5 \
  postgresql-server-dev-all

RUN pyvenv-3.4 --without-pip /opt/gather2-core-env/
RUN curl https://bootstrap.pypa.io/get-pip.py | /opt/gather2-core-env/bin/python
ADD ./gather2-core/requirements.txt /opt/gather2-core/requirements.txt
RUN  /opt/gather2-core-env/bin/pip install -r  /opt/gather2-core/requirements.txt
ADD ./gather2-core/ /opt/gather2-core/
