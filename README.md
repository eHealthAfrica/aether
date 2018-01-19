# Aether

> Survey collection and analytics

## Table of contents

- [Table of contents](#table-of-contents)
- [Setup](#Setup)
  - [Dependencies](#dependencies)
  - [Installation](#installation)
  - [Common Module](#common-module)
  - [Environment Variables](#environment-variables)
    - [Aether Kernel](#aether-kernel)
    - [Aether ODK Importer](#aether-odk-importer)
    - [Aether Couchdb Sync](#aether-couchdb-sync)
    - [Aether UI](#aether-ui)
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
git clone git@github.com:eHealthAfrica/aether.git
cd aether

docker-compose build
```

Include this entry in your `/etc/hosts` file:

```
127.0.0.1    kernel.aether.local odk.aether.local sync.aether.local ui.aether.local
```

*[Return to TOC](#table-of-contents)*

### Common module

This module contains the shared features among different containers.

To create a new version and distribute it:

```bash
./scripts/build_common_and_distribute.sh
```

See more in [README](/aether-common/README.md).

*[Return to TOC](#table-of-contents)*

### Environment Variables

Most of the environment variables are set to default values. This is the short list
of the most common ones with non default values. For more info take a look at the file
[docker-compose.yml](docker-compose.yml)


#### Aether Kernel

- `CAS_SERVER_URL`: `https://ums-dev.ehealthafrica.org` Used by UMS.
- `HOSTNAME`: `kernel.aether.local` Used by UMS.
- `RDS_DB_NAME`: `aether` Postgres database name.
- `WEB_SERVER_PORT`: `8000` Web server port.


#### Aether ODK Importer

- `CAS_SERVER_URL`: `https://ums-dev.ehealthafrica.org` Used by UMS.
- `HOSTNAME`: `odk.aether.local` Used by UMS.
- `RDS_DB_NAME`: `odk_importer` Postgres database name.
- `WEB_SERVER_PORT`: `8443` Web server port.
- `AETHER_KERNEL_TOKEN`: `a2d6bc20ad16ec8e715f2f42f54eb00cbbea2d24` Token to connect to kernel server.
- `AETHER_KERNEL_URL`: `http://kernel:8000` Aether Kernel Server url.
- `AETHER_KERNEL_URL_TEST`: `http://kernel-test:9000` Aether Kernel Server url.


#### Aether Couchdb Sync

- `CAS_SERVER_URL`: `https://ums-dev.ehealthafrica.org` Used by UMS.
- `HOSTNAME`: `sync.aether.local` Used by UMS.
- `RDS_DB_NAME`: `couchdb_sync` Postgres database name.
- `WEB_SERVER_PORT`: `8666` Web server port.
- `AETHER_KERNEL_TOKEN`: `a2d6bc20ad16ec8e715f2f42f54eb00cbbea2d24` Token to connect to kernel server.
- `AETHER_KERNEL_URL`: `http://kernel:8000` Aether Kernel Server url.
- `AETHER_KERNEL_URL_TEST`: `http://kernel-test:9000` Aether Kernel Testing Server url.
- `GOOGLE_CLIENT_ID`: `search for it in lastpass` Token used to verify the device identity with Google.


#### Aether UI

- `CAS_SERVER_URL`: `https://ums-dev.ehealthafrica.org` Used by UMS.
- `HOSTNAME`: `ui.aether.local` Used by UMS.
- `RDS_DB_NAME`: `ui` Postgres database name.
- `WEB_SERVER_PORT`: `8080` Web server port.
- `AETHER_ORG_NAME`: `eHealth Africa` Text to be displayed as page title.
- `AETHER_KERNEL_TOKEN`: `a2d6bc20ad16ec8e715f2f42f54eb00cbbea2d24` Token to connect to kernel server.
- `AETHER_KERNEL_URL`: `http://kernel:8000` Aether Kernel Server url.
- `AETHER_KERNEL_URL_TEST`: `http://kernel-test:9000` Aether Kernel Testing Server url.
- `AETHER_MODULES`: `odk-importer` Comma separated list with the available modules.
  To avoid confusion, the values will match the container name, `odk-importer`, `couchdb-sync`.
- `AETHER_ODK_TOKEN`: `d5184a044bb5acff89a76ec4e67d0fcddd5cd3a1` Token to connect to odk server.
- `AETHER_ODK_URL`: `http://odk-importer:8443` Aether ODK Importer Server url.
- `AETHER_ODK_URL_TEST`: `http://odk-importer-test:9443` Aether ODK Importer Testing Server url.


**WARNING**

Never run `odk-importer`, `couchdb-sync` or `ui` tests against any
PRODUCTION server. The tests clean up will **DELETE ALL SURVEYS!!!**

*[Return to TOC](#table-of-contents)*

## Usage

```bash
docker-compose up --build    # this will update the cointainers if needed
```

This will start:

- **aether-kernel** on `http://kernel.aether.local:8000`
  and create a superuser `admin-kernel` with the needed TOKEN.

- **odk-importer** on `http://odk.aether.local:8443`
  and create a superuser `admin-odk` with the needed TOKEN.

- **couchdb-sync** on `http://sync.aether.local:8666`
  and create a superuser `admin-sync`.

- **ui** on `http://ui.aether.local:8080`
  and create a superuser `admin-ui`.


All the created superusers have password `adminadmin` in each container.

*[Return to TOC](#table-of-contents)*

### Users & Authentication

The app defers part of the users management to
[eHA UMS tool](https://github.com/eHealthAfrica/ums).

Set the `HOSTNAME` and `CAS_SERVER_URL` environment variables if you want to
activate the UMS integration in each container.


#### UMS settings for local development

The project is `aether-all` **Aether Suite**.

The client services are:

  - **Aether Kernel (local)** for `kernel.aether.local`.
  - **Aether ODK (local)**  for `odk.aether.local`.
  - **Aether Sync (local)** for `sync.aether.local`.
  - **Aether UI (local)**   for `ui.aether.local`.


Other options are to log in via token, via basic authentication or via the
standard django authentication process in the admin section.
The available options depend on each container.

*[Return to TOC](#table-of-contents)*

#### Token Authentication

The communication between the containers is done via
[token authentication](http://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication).

In the case of `aether-odk-importer` and `aether-couchdb-sync` there is a
global token to connect to `aether-kernel` set in the **required** environment
variable `AETHER_KERNEL_TOKEN`.

In the case of `aether-ui` there are tokens per user. This means that every time
a logged in user tries to visit any page that requires to fetch data from any of
the other apps, `aether-kernel` and/or `aether-odk-importer`, the system will verify
that the user token for that app is valid or will request a new one using the
global tokens, `AETHER_KERNEL_TOKEN` and/or `AETHER_ODK_TOKEN`; that's going to
be used for all requests and will allow the system to better track the user actions.

*[Return to TOC](#table-of-contents)*


## Development

All development should be tested within the container, but developed in the host folder.
Read the `docker-compose.yml` file to see how it's mounted.

*[Return to TOC](#table-of-contents)*


## Deployment

Set the `HOSTNAME` and `CAS_SERVER_URL` environment variables if you want to
activate the UMS integration in each container.

Set the `AETHER_KERNEL_TOKEN` and `AETHER_KERNEL_URL` environment variables when
starting the `aether-odk-importer` to have ODK Collect submissions posted to
Aether Kernel.

If a valid `AETHER_KERNEL_TOKEN` and `AETHER_KERNEL_URL` combination is not set,
the server will still start, but ODK Collect submissions will fail.

To check if it is possible to connect to Aether Kernel with those variables
visit the entrypoint `/check-kernel` in the odk server (no credentials needed).
If the response is `Always Look on the Bright Side of Life!!!`
it's not possible to connect, on the other hand if the message is
`Brought to you by eHealth Africa - good tech for hard places` everything goes fine.

This also applies for `aether-couchdb-sync` and `aether-ui`.

In the case of `aether-couchdb-sync` a valid `GOOGLE_CLIENT_ID`
environment variable is necessary to verify the device credentials as well.

Infrastructure deployment is done with Terraform, which configuration
files are stored in [terraform](terraform) directory.

Application deployment is managed by AWS Elastic Container Service and is
being done automatically on the following branches/environments:

- branch `develop` is deployed to `dev` environment.
  [![Build Status](https://travis-ci.com/eHealthAfrica/aether.svg?token=Rizk7xZxRNoTexqsQfXy&branch=develop)](https://travis-ci.com/eHealthAfrica/aether)

- branch `master` is deployed to `prod` environment.
  [![Build Status](https://travis-ci.com/eHealthAfrica/aether.svg?token=Rizk7xZxRNoTexqsQfXy&branch=master)](https://travis-ci.com/eHealthAfrica/aether)

- branch `lake-chad-basin` is deployed to `lake chad basin` environment.
  [![Build Status](https://travis-ci.com/eHealthAfrica/aether.svg?token=Rizk7xZxRNoTexqsQfXy&branch=lake-chad-basin)](https://travis-ci.com/eHealthAfrica/aether)

*[Return to TOC](#table-of-contents)*


## Containers and services

The list of the main containers:


| Container         | Description                                                             |
| ----------------- | ----------------------------------------------------------------------- |
| db                | [PostgreSQL](https://www.postgresql.org/) database                      |
| couchdb           | [CouchDB](http://couchdb.apache.org/) database for sync                 |
| redis             | [Redis](https://redis.io/) for task queueing and task result storage    |
| **kernel**          | Aether Kernel app                                                        |
| **odk-importer**  | Aether ODK Collect Adapter app (imports data from ODK Collect)         |
| **couchdb-sync**  | Aether Couchdb Sync app (imports data from Aether Mobile app)         |
| **ui**            | Aether UI app                                                          |
| couchdb-sync-rq   | [RQ python](http://python-rq.org/) task runner to perform sync jobs     |
| kernel-test         | Aether Kernel TESTING app (used only in e2e tests with other containers) |
| common-test       | Aether Common module (only for tests)                                  |


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
./scripts/test_with_kernel.sh <container-name>
```

**WARNING**

Never run `odk-importer`, `couchdb-sync` or `ui` tests against any
PRODUCTION server. The tests clean up will **DELETE ALL SURVEYS!!!**

Look into [docker-compose.yml](docker-compose.yml) or
[docker-compose-test.yml](docker-compose-test.yml), the variable
`AETHER_KERNEL_URL_TEST` indicates the Aether Kernel Server used in tests.

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
This also rebuilds `aether.common` module and distributes it within the containers.
Do not forget to include new containers in the file.

or

```bash
docker-compose run <container-name> pip_freeze
```
In this case `aether.common` is not rebuilt.

*[Return to TOC](#table-of-contents)*


### Enketo setup

First, start all containers:

```
docker-compose up --build
```

This will start an enketo transformer service running on port 8085. It can be accessed via the `enketo` view on the ODK module, which takes an id of an xform that should be displayed. This view transforms the xform by posting it to the transfomer (which listens on port 8085), and then displays the result via a minimal version of the Enketo app, which is in `odk-importer/enketo/`.

TODO: make the build process work
TODO: form validation and submission

