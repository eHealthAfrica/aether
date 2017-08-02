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

### Environment Variables

Most of the environment variables are set to default values. This is the short list
of the most common ones with non-default values. For more info take a look at the file
[docker-compose.yml](docker-compose.yml)

#### Gather Core

- `RDS_DB_NAME`: `gather2` Postgres database name.
- `WEB_SERVER_PORT`: `8000` Web server port.


#### Gather ODK Importer

- `RDS_DB_NAME`: `odk_importer` Postgres database name.
- `WEB_SERVER_PORT`: `8443` Web server port.
- `GATHER_CORE_TOKEN`: `a2d6bc20ad16ec8e715f2f42f54eb00cbbea2d24` Token to connect to core server.
- `GATHER_CORE_URL`: `http://core:8000` Gather Core Server url.
- `GATHER_CORE_URL_TEST`: `http://core-test:9000` Gather Core Server url.


#### Gather Couchdb Sync

- `RDS_DB_NAME`: `couchdb_sync` Postgres database name.
- `WEB_SERVER_PORT`: `8666` Web server port.
- `GATHER_CORE_TOKEN`: `a2d6bc20ad16ec8e715f2f42f54eb00cbbea2d24` Token to connect to core server.
- `GATHER_CORE_URL`: `http://core:8000` Gather Core Server url.
- `GATHER_CORE_URL_TEST`: `http://core-test:9000` Gather Core Testing Server url.
- `GOOGLE_CLIENT_ID`: `search for it in lastpass` Token used to verify the device identity with Google.


**WARNING**
Never run `odk-importer` or `coucdhb-sync` tests against any PRODUCTION server.
The tests clean up will DELETE ALL SURVEYS!!!


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
| **odk-importer**  | Gather2 ODK Collect Adapter app (imports data from ODK Collect)         |
| **couchdb-sync**  | Gather2 Couchdb Sync app (imports data from Gather2 Mobile app)         |
| couchdb-sync-rq   | [RQ python](http://python-rq.org/) task runner to perform sync jobs     |
| core-test         | Gather2 Core TESTING app (used only in e2e tests with other containers) |


All of the containers definition for development can be found in the
[docker-compose.yml](docker-compose.yml) file.


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

**WARNING**
Never run `odk-importer` or `coucdhb-sync` tests against a
PRODUCTION server. The tests clean up will DELETE ALL SURVEYS!!!

Look into [docker-compose.yml](docker-compose.yml), the variable
`GATHER_CORE_URL_TEST` indicates the Gather Core Server used in tests.


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
