# Gather2

> Survey collection and analytics


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
docker-compose up
```

This will start:

- **gather-core** on `0.0.0.0:8000` and create a superuser `admin-core` with the needed TOKEN.
- **odk-importer** on `0.0.0.0:8443` and create a superuser `admin-odk`.
- **couchdb-sync** on `0.0.0.0:8666` and create a superuser `admin-sync`.

All the created superusers have password `adminadmin` in each container.


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

In the case of `gather2-couchdb-sync` also a valid `GOOGLE_CLIENT_ID`
environment variable is necessary to verify the device credentials.

Infrastructure deployment is done with Terraform, which configuration
files are stored in [terraform](terraform) directory.

Application deployment is managed by AWS Elastic Container Service and is
being done automatically on the following branches/environments:

- branch `develop` is deployed to `dev` environment.
  [![Build Status](https://travis-ci.com/eHealthAfrica/gather2.svg?token=Rizk7xZxRNoTexqsQfXy&branch=develop)](https://travis-ci.com/eHealthAfrica/gather2)

- branch `master` is deployed to `prod` environment.
  [![Build Status](https://travis-ci.com/eHealthAfrica/gather2.svg?token=Rizk7xZxRNoTexqsQfXy&branch=master)](https://travis-ci.com/eHealthAfrica/gather2)

- branch `lake-chad-basin` is deployed to `lake chad basin` environment.
  [![Build Status](https://travis-ci.com/eHealthAfrica/gather2.svg?token=Rizk7xZxRNoTexqsQfXy&branch=lake-chad-basin)](https://travis-ci.com/eHealthAfrica/gather2)



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
./scripts/test_all.sh
```

or

```bash
docker-compose run core         test
docker-compose run odk-importer test
docker-compose run couchdb-sync test
```

or

```bash
docker-compose run core         test_lint
docker-compose run odk-importer test_lint
docker-compose run couchdb-sync test_lint

docker-compose run core         test_coverage
docker-compose run odk-importer test_coverage
docker-compose run couchdb-sync test_coverage
```


### Upgrade python dependencies

#### Check outdated dependencies

```bash
docker-compose run core         eval pip list --outdated
docker-compose run odk-importer eval pip list --outdated
docker-compose run couchdb-sync eval pip list --outdated
```

#### Update requirements file

```bash
./scripts/upgrade_all.sh
```

or

```bash
docker-compose run core         pip_freeze
docker-compose run odk-importer pip_freeze
docker-compose run couchdb-sync pip_freeze
```
