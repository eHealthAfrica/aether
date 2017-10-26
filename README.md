# Gather2

> Survey collection and analytics

## Table of contents

- [Table of contents](#table-of-contents)
- [Setup](#Setup)
  - [Dependencies](#dependencies)
  - [Installation](#installation)
  - [Common Module](#common-module)
  - [Environment Variables](#environment-variables)
    - [Gather Core](#gather-core)
    - [Gather ODK Importer](#gather-odk-importer)
    - [Gather Couchdb Sync](#gather-couchdb-sync)
    - [Gather UI](#gather-ui)
- [Usage](#usage)
  - [Users & Authentication](#users--authentication)
    - [UMS settings for local development](#ums-settings-for-local-development)
    - [Token Authentication](#token-authentication)
- [Development](#development)
- [Deployment](#deployment)
- [Containers and services](#containers-and-services)
- [Run commands in the containers](#run-commands-in-the-containers)
  - [Run tests](#run-tests)
  - [Upgrade python dependencies](#upgrade-python-dependencies)
    - [Check outdated dependencies](#check-outdated-dependencies)
    - [Update requirements file](#update-requirements-file)


## Setup

### Dependencies

- git
- [docker-compose](https://docs.docker.com/compose/)

*[Return to TOC](#table-of-contents)*

### Installation

```bash
git clone git@github.com:eHealthAfrica/gather2.git
cd gather2

docker-compose build
```

Include this entry in your `/etc/hosts` file:

```
127.0.0.1    core.gather2.local odk.gather2.local sync.gather2.local ui.gather2.local
```

*[Return to TOC](#table-of-contents)*

### Common module

This module contains the shared features among different containers.

To create a new version and distribute it:

```bash
./scripts/build_common_and_distribute.sh
```

See more in [README](/gather2-common/README.md).

*[Return to TOC](#table-of-contents)*

### Environment Variables

Most of the environment variables are set to default values. This is the short list
of the most common ones with non default values. For more info take a look at the file
[docker-compose.yml](docker-compose.yml)


#### Gather Core

- `CAS_SERVER_URL`: `https://ums-dev.ehealthafrica.org` Used by UMS.
- `HOSTNAME`: `core.gather2.local` Used by UMS.
- `RDS_DB_NAME`: `gather2` Postgres database name.
- `WEB_SERVER_PORT`: `8000` Web server port.


#### Gather ODK Importer

- `CAS_SERVER_URL`: `https://ums-dev.ehealthafrica.org` Used by UMS.
- `HOSTNAME`: `odk.gather2.local` Used by UMS.
- `RDS_DB_NAME`: `odk_importer` Postgres database name.
- `WEB_SERVER_PORT`: `8443` Web server port.
- `GATHER_CORE_TOKEN`: `a2d6bc20ad16ec8e715f2f42f54eb00cbbea2d24` Token to connect to core server.
- `GATHER_CORE_URL`: `http://core:8000` Gather Core Server url.
- `GATHER_CORE_URL_TEST`: `http://core-test:9000` Gather Core Server url.


#### Gather Couchdb Sync

- `CAS_SERVER_URL`: `https://ums-dev.ehealthafrica.org` Used by UMS.
- `HOSTNAME`: `sync.gather2.local` Used by UMS.
- `RDS_DB_NAME`: `couchdb_sync` Postgres database name.
- `WEB_SERVER_PORT`: `8666` Web server port.
- `GATHER_CORE_TOKEN`: `a2d6bc20ad16ec8e715f2f42f54eb00cbbea2d24` Token to connect to core server.
- `GATHER_CORE_URL`: `http://core:8000` Gather Core Server url.
- `GATHER_CORE_URL_TEST`: `http://core-test:9000` Gather Core Testing Server url.
- `GOOGLE_CLIENT_ID`: `search for it in lastpass` Token used to verify the device identity with Google.


#### Gather UI

- `CAS_SERVER_URL`: `https://ums-dev.ehealthafrica.org` Used by UMS.
- `HOSTNAME`: `ui.gather2.local` Used by UMS.
- `RDS_DB_NAME`: `ui` Postgres database name.
- `WEB_SERVER_PORT`: `8080` Web server port.
- `GATHER_ORG_NAME`: `eHealth Africa` Text to be displayed as page title.
- `GATHER_CORE_TOKEN`: `a2d6bc20ad16ec8e715f2f42f54eb00cbbea2d24` Token to connect to core server.
- `GATHER_CORE_URL`: `http://core:8000` Gather Core Server url.
- `GATHER_CORE_URL_TEST`: `http://core-test:9000` Gather Core Testing Server url.
- `GATHER_MODULES`: `odk-importer` Comma separated list with the available modules.
  To avoid confusion, the values will match the container name, `odk-importer`, `couchdb-sync`.
- `GATHER_ODK_TOKEN`: `d5184a044bb5acff89a76ec4e67d0fcddd5cd3a1` Token to connect to odk server.
- `GATHER_ODK_URL`: `http://odk-importer:8443` Gather ODK Importer Server url.
- `GATHER_ODK_URL_TEST`: `http://odk-importer-test:9443` Gather ODK Importer Testing Server url.


**WARNING**

Never run `odk-importer`, `couchdb-sync` or `ui` tests against any
PRODUCTION server. The tests clean up will **DELETE ALL SURVEYS!!!**

*[Return to TOC](#table-of-contents)*

## Usage

```bash
docker-compose up --build    # this will update the cointainers if needed
```

This will start:

- **gather-core** on `http://core.gather2.local:8000`
  and create a superuser `admin-core` with the needed TOKEN.

- **odk-importer** on `http://odk.gather2.local:8443`
  and create a superuser `admin-odk` with the needed TOKEN.

- **couchdb-sync** on `http://sync.gather2.local:8666`
  and create a superuser `admin-sync`.

- **ui** on `http://ui.gather2.local:8080`
  and create a superuser `admin-ui`.


All the created superusers have password `adminadmin` in each container.

*[Return to TOC](#table-of-contents)*

### Users & Authentication

The app defers part of the users management to
[eHA UMS tool](https://github.com/eHealthAfrica/ums).

Set the `HOSTNAME` and `CAS_SERVER_URL` environment variables if you want to
activate the UMS integration in each container.


#### UMS settings for local development

The project is `gather2-all` **Gather2 Suite**.

The client services are:

  - **Gather2 Core (local)** for `core.gather2.local`.
  - **Gather2 ODK (local)**  for `odk.gather2.local`.
  - **Gather2 Sync (local)** for `sync.gather2.local`.
  - **Gather2 UI (local)**   for `ui.gather2.local`.


Other options are to log in via token, via basic authentication or via the
standard django authentication process in the admin section.
The available options depend on each container.

*[Return to TOC](#table-of-contents)*

#### Token Authentication

The communication between the containers is done via
[token authentication](http://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication).

In the case of `gather2-odk-importer` and `gather2-couchdb-sync` there is a
global token to connect to `gather2-core` set in the **required** environment
variable `GATHER_CORE_TOKEN`.

In the case of `gather2-ui` there are tokens per user. This means that every time
a logged in user tries to visit any page that requires to fetch data from any of
the other apps, `gather2-core` and/or `gather2-odk-importer`, the system will verify
that the user token for that app is valid or will request a new one using the
global tokens, `GATHER_CORE_TOKEN` and/or `GATHER_ODK_TOKEN`; that's going to
be used for all requests and will allow the system to better track the user actions.

*[Return to TOC](#table-of-contents)*


## Development

All development should be tested within the container, but developed in the host folder.
Read the `docker-compose.yml` file to see how it's mounted.

*[Return to TOC](#table-of-contents)*


## Deployment

Set the `HOSTNAME` and `CAS_SERVER_URL` environment variables if you want to
activate the UMS integration in each container.

Set the `GATHER_CORE_TOKEN` and `GATHER_CORE_URL` environment variables when
starting the `gather2-odk-importer` to have ODK Collect submissions posted to
Gather2 Core.

If a valid `GATHER_CORE_TOKEN` and `GATHER_CORE_URL` combination is not set,
the server will still start, but ODK Collect submissions will fail.

To check if it is possible to connect to Gather2 Core with those variables
visit the entrypoint `/check-core` in the odk server (no credentials needed).
If the response is `Always Look on the Bright Side of Life!!!`
it's not possible to connect, on the other hand if the message is
`Brought to you by eHealth Africa - good tech for hard places` everything goes fine.

This also applies for `gather2-couchdb-sync` and `gather2-ui`.

In the case of `gather2-couchdb-sync` a valid `GOOGLE_CLIENT_ID`
environment variable is necessary to verify the device credentials as well.

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

*[Return to TOC](#table-of-contents)*


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
| **ui**            | Gather2 UI app                                                          |
| couchdb-sync-rq   | [RQ python](http://python-rq.org/) task runner to perform sync jobs     |
| core-test         | Gather2 Core TESTING app (used only in e2e tests with other containers) |
| common-test       | Gather2 Common module (only for tests)                                  |


All of the containers definition for development can be found in the
[docker-compose.yml](docker-compose.yml) file.

*[Return to TOC](#table-of-contents)*


## Run commands in the containers

Each docker container uses the same script as entrypoint. The `entrypoint.sh`
script offers a range of commands to start services or run commands.
The full list of commands can be seen in the script.

The pattern to run a command is always
``docker-compose run <container-name> <entrypoint-command> <...args>``

*[Return to TOC](#table-of-contents)*


### Run tests

This will stop ALL running containers and execute the containers tests.

```bash
./scripts/test_all.sh
```

To execute tests in just one container.

```bash
docker-compose run <container-name> test

```

or

```bash
docker-compose run <container-name> test_lint
docker-compose run <container-name> test_coverage
```

The e2e tests are run against different containers, the config file used
for them is [docker-compose-test.yml](docker-compose-test.yml).

Before running `odk-importer`, `couchdb-sync` or `ui` you should start
the needed test containers.

```bash
docker-compose -f docker-compose-test.yml up -d <container-name>-test
```

This script will start the auxiliary containers and execute the tests
in `odk-importer` or `couchdb-sync`.

```bash
./scripts/test_with_core.sh <container-name>
```

**WARNING**

Never run `odk-importer`, `couchdb-sync` or `ui` tests against any
PRODUCTION server. The tests clean up will **DELETE ALL SURVEYS!!!**

Look into [docker-compose.yml](docker-compose.yml) or
[docker-compose-test.yml](docker-compose-test.yml), the variable
`GATHER_CORE_URL_TEST` indicates the Gather Core Server used in tests.

*[Return to TOC](#table-of-contents)*


### Upgrade python dependencies

#### Check outdated dependencies

```bash
docker-compose run <container-name> eval pip list --outdated
```

#### Update requirements file

```bash
./scripts/upgrade_all.sh
```
This also rebuilds `gather2.common` module and distributes it within the containers.
Do not forget to include new containers in the file.

or

```bash
docker-compose run <container-name> pip_freeze
```
In this case `gather2.common` is not rebuilt.

*[Return to TOC](#table-of-contents)*
