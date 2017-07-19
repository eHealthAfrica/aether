FROM ubuntu:14.04

ENV TERM screen-256color

RUN locale-gen --no-purge en_US.UTF-8
ENV LC_ALL en_US.UTF-8
RUN update-locale LANG=en_US.UTF-8
RUN useradd -ms /bin/false gather2

RUN apt-get update -qq && apt-get install -y wget

RUN sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ `lsb_release -cs`-pgdg main" >> /etc/apt/sources.list.d/pgdg.list'
RUN wget -q https://www.postgresql.org/media/keys/ACCC4CF8.asc -O - | sudo apt-key add -

COPY ./conf/apt-packages.txt /tmp/apt-packages.txt
RUN apt-get update -qq && cat /tmp/apt-packages.txt | xargs apt-get -qq --yes --force-yes install

RUN pip3 install virtualenv
RUN virtualenv -p python3 /var/env/

COPY ./requirements.txt /code/requirements.txt
COPY ./dependencies /code/dependencies
RUN /var/env/bin/pip install -f /code/dependencies -r /code/requirements.txt

WORKDIR /code

ADD ./ /code
RUN chown -R gather2: /code

ENTRYPOINT ["/code/entrypoint.sh"]
