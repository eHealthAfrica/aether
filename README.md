# Gather2

> Survey collection and analytics

[![Build Status](https://travis-ci.org/eHealthAfrica/gather2.svg?branch=master)](https://travis-ci.org/eHealthAfrica/gather2)

## Setup

### Dependencies

- git
- [docker-compose](https://docs.docker.com/compose/)

### Installation

```
$ git clone git@github.com:eHealthAfrica/gather2.git
$ cd gather2

$ docker-compose up -d db  # Or run this in a different tab without `-d` to make it easy to reset the db
$ docker-compose run core manage test core
$ docker-compose run core setuplocaldb
$ docker-compose run --service-ports core manage runserver 0.0.0.0:8000
```

## Usage

Below command will print out available entrypoint commands:
```
$ docker-compose run core /code/gather2-core/entrypoint.sh
```

## Development

All development should be tested within the container, but developed in the host folder. Read the `docker-compose.yml` file to see how it's mounted.
```
$ docker-compose run core bash
root@localhost:/#
```

## Deployment

Infrastructure deployment is done with AWS CloudFormation, which configuration files are stored in [cloudformation](cloudformation) directory.

Application deployment is managed by AWS Beanstalk and is being done automatically on the following branches/environments:
- branch `master` is deployed to `dev` environment: [gather2-dev.ehealthafrica.org](https://gather2-dev.ehealthafrica.org)

All the logs are forwarded to CloudWatch Logs to be easily accessible for developers
