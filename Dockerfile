FROM ubuntu:14.04


RUN apt-get install -y wget
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main 9.4" > /etc/apt/sources.list.d/pgdg.list

RUN apt-get update && apt-get -y upgrade && apt-get install -y \
  git \
  python3-dev \
  python3-pip \
  postgresql-client-9.4 \
  postgresql-server-dev-9.4

RUN pip3 install virtualenv uwsgi

RUN virtualenv /opt/gather2/venv/

ADD ./requirements.txt /opt/gather2/requirements.txt
RUN /opt/gather2/venv/bin/pip install --src /tmp -r /opt/gather2/requirements.txt

ADD . /tmp/gather2_src/
RUN /opt/gather2/venv/bin/pip install /tmp/gather2_src/
RUN rm -r /tmp/gather2_src

EXPOSE 8080

ENV DATABASE_URL ""
ENV DJANGO_CONFIGURATION Docker
ENV DJANGO_SETTINGS_MODULE gather2_core.settings
ENV DJANGO_ALLOWED_HOSTS ""

COPY ./docker-entrypoint.sh /opt/gather2/
RUN chmod +x /opt/gather2/docker-entrypoint.sh
ENTRYPOINT ["/opt/gather2/docker-entrypoint.sh"]
CMD ["serve"]

RUN /opt/gather2/docker-entrypoint.sh manage collectstatic --no-input

USER www-data

