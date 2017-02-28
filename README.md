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

$ docker-compose build
$ docker-compose run core setuplocaldb
$ docker-compose run odk-importer setuplocaldb
```

### Setup

The only thing that you need now is a superuser!
```
docker-compose run core manage createsuperuser
docker-compose run odk-importer manage createsuperuser
```

## Usage

This will start the gather-core 0.0.0.0:8000 and the odk-importer on 0.0.0.0:8443


```
$ docker-compose up
```

## Development

All development should be tested within the container, but developed in the host folder. Read the `docker-compose.yml` file to see how it's mounted.
```
$ docker-compose run core bash
root@localhost:/#
```

## Deployment

Set the `GATHER_CORE_TOKEN` and `GATHER_CORE_URL` environment variables when starting the `gather2-odk-importer` to have ODK Collect submissions posted to Gather2 Core.
If a valid `GATHER_CORE_TOKEN` and `GATHER_CORE_URL` combination is not set, the server will still start, but ODK Collection submissions will fail.

When deploying set the env var `DJANGO_S3_FILE_STORAGE` to True. See `settings.py` for the other available settings.

Infrastructure deployment is done with AWS CloudFormation, which configuration files are stored in [cloudformation](cloudformation) directory.

Application deployment is managed by AWS Beanstalk and is being done automatically on the following branches/environments:
- branch `master` is deployed to `dev` environment: [gather2-dev.ehealthafrica.org](https://gather2-dev.ehealthafrica.org)

All the logs are forwarded to CloudWatch Logs to be easily accessible for developers
