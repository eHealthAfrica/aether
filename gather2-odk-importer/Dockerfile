FROM ubuntu:14.04

RUN locale-gen --no-purge en_US.UTF-8
ENV LC_ALL en_US.UTF-8
RUN update-locale LANG=en_US.UTF-8

RUN apt-get update -qq && apt-get install -y wget
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main 9.4" > /etc/apt/sources.list.d/pgdg.list

ADD requirements.txt /code/requirements.txt
ADD apt-packages.txt /code/apt-packages.txt

RUN apt-get update -qq && apt-get install -y wget
RUN cat /code/apt-packages.txt | xargs apt-get --yes --force-yes install
RUN pip3 install virtualenv

RUN virtualenv -p python3 /var/env/
COPY ./dependencies /code/dependencies
RUN /var/env/bin/pip install -f /code/dependencies -r /code/requirements.txt
RUN /var/env/bin/pip install -r /code/requirements.txt

WORKDIR /code

ADD ./ /code/

ENTRYPOINT ["bash", "/code/entrypoint.sh"]
CMD ["manage", "runserver", "0.0.0.0:8443"]
