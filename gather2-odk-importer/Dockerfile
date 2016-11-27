FROM ubuntu:14.04

RUN apt-get install -y wget
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main 9.4" > /etc/apt/sources.list.d/pgdg.list

COPY apt-packages.txt /code/apt-packages.txt
RUN apt-get update -qq && cat /code/apt-packages.txt | xargs apt-get --yes --force-yes install

COPY requirements.txt /code/requirements.txt

RUN pip3 install virtualenv
RUN virtualenv ~/env/
RUN ~/env/bin/pip install -r /code/requirements.txt

WORKDIR /code

ADD ./ /code/
