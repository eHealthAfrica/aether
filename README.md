# Gather2

> Survey collection and analytics

[![Build Status](https://travis-ci.org/eHealthAfrica/gather2.svg?branch=master)](https://travis-ci.org/eHealthAfrica/gather2)

## Setup

### Dependencies

- git
- [docker-compose](https://docs.docker.com/compose/)

### Installation

```bash
git clone git@github.com:eHealthAfrica/gather2.git
cd gather2

docker-compose build
```

## Usage

```bash
export GATHER_CORE_TOKEN=a2d6bc20ad16ec8e715f2f42f54eb00cbbea2d24
docker-compose up
```

This will start:

- **gather-core** on `0.0.0.0:8000`
- **odk-importer** on `0.0.0.0:8443`
- **couchdb-sync** on `0.0.0.0:8666`

Also create (in DEV mode) a superuser `admin` with password `adminadmin` in each container
and the needed TOKEN in `gather-core` too.

## Development

All development should be tested within the container, but developed in the host folder.
Read the `docker-compose.yml` file to see how it's mounted.

## Deployment

Set the `GATHER_CORE_TOKEN` and `GATHER_CORE_URL` environment variables when
starting the `gather2-odk-importer` to have ODK Collect submissions posted to
Gather2 Core.

If a valid `GATHER_CORE_TOKEN` and `GATHER_CORE_URL` combination is not set,
the server will still start, but ODK Collection submissions will fail.

This also applies for `gather2-couchdb-sync`.

Infrastructure deployment is done with Terraform, which configuration
files are stored in [terraform](terraform) directory.

Application deployment is managed by AWS Elastic Container Service and is being done automatically
on the following branches/environments:
- branch `master` is deployed to `dev` environment:
  [gather2-dev.ehealthafrica.org](https://gather2-dev.ehealthafrica.org)

All the logs are forwarded to CloudWatch Logs to be easily accessible for developers.


## Containers and services

The list of the main containers:


| Container         | Description                                                             |
| ----------------- | ----------------------------------------------------------------------- |
| db                | [PostgreSQL](https://www.postgresql.org/) database                      |
| couchdb           | [CouchDB](http://couchdb.apache.org/) database for sync                 |
| redis             | [Redis](https://redis.io/) for task queueing and task result storage    |
| **core**          | Gather2 Core app                                                        |
| **odk-importer**  | ODK Collect Adapter app (imports data from ODK Collect)                 |
| **couchdb-sync**  | Sync app (imports data from Gather2 Mobile app)                         |
| couchdb-sync-rq   | [RQ python](http://python-rq.org/) task runner to perform sync jobs     |


All of the containers definition for development can be found in the `docker-compose.yml`.


## Run commands on the server

Each docker container uses the same script as entrypoint. The `entrypoint.sh`
script offers a range of commands to start services or run commands.
The full list of commands can be seen in the script.

The pattern to run a command is always
``docker-compose run <container-name> <entrypoint-command> <...args>``


### Run tests

```bash
docker-compose run core test_lint
docker-compose run odk-importer test_lint
docker-compose run couchdb-sync test_lint

docker-compose run core test_coverage
docker-compose run odk-importer test_coverage
docker-compose run couchdb-sync test_coverage
```

### Upgrade python dependencies

```bash
docker-compose run core pip_freeze
docker-compose run odk-importer pip_freeze
docker-compose run couchdb-sync pip_freeze
```
