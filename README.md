# Gather2

> Survey collection and analytics

[![Build Status](https://travis-ci.org/eHealthAfrica/gather2.svg?branch=master)](https://travis-ci.org/eHealthAfrica/gather2)

## Setup

### Dependencies

git

[docker-compose](https://docs.docker.com/compose/)

### Installation

```
$ git clone git@github.com:eHealthAfrica/gather2.git
$ cd gather2

$ sudo docker-compose up -d db  # Or run this in a different tab without `-d` to make it easy to reset the db
$ sudo docker-compose run core manage test core
$ sudo docker-compose run core setuplocaldb
$ sudo docker-compose run --service-ports core manage runserver 0.0.0.0:8000
```

## Usage

```
$ sudo docker-compose run core /code/gather2-core/entrypoint.sh


Commands
serve      : Serve the application with uwsgi
manage     : Invoke django manage.py commands
sqlcreate  : Create empty database for Gather2, will still need migrations run
```

## Development

All development should be tested within the container, but developed in the host folder. Read the `docker-compose.yml` file to see how it's mounted.
```
$ sudo docker-compose run core bash
root@localhost:/#
```

## Monitoring

On production environment, supervisord starts filebeat, a software that sends the log specified in `gather2-core/conf/filebeat.yml` line 15 to a remote logstash server, specified in line 227.

## Elastic Beanstalk Setup

```
$ cd gather2-core
```

1. Create a new beanstalk environment with a RDS istance
2. Rename `Dockerrun.aws.json.tmlp` to `Dockerrun.aws.json`
3. Set the RDS variables on the `Dockerrun.aws.json` file
4. Copy `conf/nginx.gathercore.conf.tmpl` to `conf/nginx.gathercore.conf`
5. Edit the `conf/nginx.gathercore.conf` to match the ElasticBeanstalk environment's url (line 3, `server_name` variable)
6. Edit the `conf/logstash.conf` to match your credentials and the Elasticsearch's url
7. Deploy
