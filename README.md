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
$ sudo docker-compose run core /code/gather2-core/entrypoint.sh manage test core
$ sudo docker-compose run core /code/gather2-core/entrypoint.sh sqlcreate
$ sudo docker-compose run core /code/gather2-core/entrypoint.sh manage migrate
$ sudo docker-compose run -p 8000:8000 core /code/gather2-core/entrypoint.sh manage runserver 0.0.0.0:8000
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
