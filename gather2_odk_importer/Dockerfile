FROM ubuntu:14.04

ENV HOME /root
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get install -y wget
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main 9.4" > /etc/apt/sources.list.d/pgdg.list

ADD requirements_importer.txt /tmp/requirements.txt
ADD apt-packages.txt /tmp/apt-packages.txt
ADD conf/startup.sh /usr/local/bin/startupimporter.sh

RUN chmod +x /usr/local/bin/startupimporter.sh

RUN locale-gen --no-purge en_US.UTF-8
ENV LC_ALL en_US.UTF-8
RUN update-locale LANG=en_US.UTF-8

RUN apt-get update -qq
RUN cat /tmp/apt-packages.txt | xargs apt-get --yes --force-yes install

RUN pip install -r /tmp/requirements.txt

WORKDIR /code

ADD ./ /code/

EXPOSE 8000
