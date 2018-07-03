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
    - [Aether ODK Module](#aether-odk-module)
    - [Aether CouchDB Sync Module](#aether-couchdb-sync-module)
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

### Installation of a local development environment

```bash
git clone git@github.com:eHealthAfrica/aether.git
cd aether
docker-compose build
docker-compose up
```

**NOTE**: the docker-compose files are intended for local development only. They contain hardcoded credentials TODO: more details

Include this entry in your `/etc/hosts` file:

```
127.0.0.1    kernel.aether.local odk.aether.local sync.aether.local
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
[docker-compose-base.yml](docker-compose-base.yml)


#### Aether Kernel

- `CAS_SERVER_URL`: `https://ums-dev.ehealthafrica.org` Used by UMS.
- `HOSTNAME`: `kernel.aether.local` Used by UMS.
- `RDS_DB_NAME`: `aether` Postgres database name.
- `WEB_SERVER_PORT`: `8000` Web server port.
- `AETHER_KERNEL_TOKEN`: `a2d6bc20ad16ec8e715f2f42f54eb00cbbea2d24`
  to connect to it from other modules. It's used within the start up scripts.


#### Aether ODK Module

- `CAS_SERVER_URL`: `https://ums-dev.ehealthafrica.org` Used by UMS.
- `HOSTNAME`: `odk.aether.local` Used by UMS.
- `RDS_DB_NAME`: `odk` Postgres database name.
- `WEB_SERVER_PORT`: `8443` Web server port.
- `AETHER_KERNEL_TOKEN`: `a2d6bc20ad16ec8e715f2f42f54eb00cbbea2d24` Token to connect to kernel server.
- `AETHER_KERNEL_URL`: `http://kernel:8000` Aether Kernel Server url.
- `AETHER_KERNEL_URL_TEST`: `http://kernel-test:9000` Aether Kernel Testing Server url.
- `AETHER_ODK_TOKEN`: `d5184a044bb5acff89a76ec4e67d0fcddd5cd3a1`
  to connect to it from other modules. It's used within the start up scripts.


#### Aether CouchDB Sync Module

- `CAS_SERVER_URL`: `https://ums-dev.ehealthafrica.org` Used by UMS.
- `HOSTNAME`: `sync.aether.local` Used by UMS.
- `RDS_DB_NAME`: `couchdb-sync` Postgres database name.
- `WEB_SERVER_PORT`: `8666` Web server port.
- `AETHER_KERNEL_TOKEN`: `a2d6bc20ad16ec8e715f2f42f54eb00cbbea2d24` Token to connect to kernel server.
- `AETHER_KERNEL_URL`: `http://kernel:8000` Aether Kernel Server url.
- `AETHER_KERNEL_URL_TEST`: `http://kernel-test:9000` Aether Kernel Testing Server url.
- `GOOGLE_CLIENT_ID`: `search for it in lastpass` Token used to verify the device identity with Google.


**WARNING**

Never run `odk` or `couchdb-sync` tests against any PRODUCTION server.
The tests clean up will **DELETE ALL MAPPINGS!!!**

*[Return to TOC](#table-of-contents)*

## Usage

```bash
docker-compose up --build    # this will update the containers if needed
```

or

```bash
./scripts/docker_start.sh    # starts all
```

This will start:

- **Aether Kernel** on `http://kernel.aether.local:8000`
  and create a superuser `admin` with the needed TOKEN.

- **Aether ODK Module** on `http://odk.aether.local:8443`
  and create a superuser `admin` with the needed TOKEN.

- **Aether CouchDB Sync Module** on `http://sync.aether.local:8666`
  and create a superuser `admin`.


All the created superusers have password `adminadmin` in each container.


To start any app/module separately:

```bash
./scripts/docker_start.sh kernel          # starts Aether Kernel app and its dependencies

./scripts/docker_start.sh odk             # starts Aether ODK module and its dependencies

./scripts/docker_start.sh couchdb-sync    # starts Aether CouchDB Sync module and its dependencies
```

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

Other options are to log in via token, via basic authentication or via the
standard django authentication process in the admin section.
The available options depend on each container.

*[Return to TOC](#table-of-contents)*

#### Token Authentication

The communication between the containers is done via
[token authentication](http://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication).

In the case of `aether-odk-module` and `aether-couchdb-sync-module` there is a
global token to connect to `aether-kernel` set in the **required** environment
variable `AETHER_KERNEL_TOKEN`.

In the case of `aether-ui` there are tokens per user. This means that every time
a logged in user tries to visit any page that requires to fetch data from any of
the other apps, `aether-kernel` and/or `aether-odk-module`, the system will verify
that the user token for that app is valid or will request a new one using the
global tokens, `AETHER_KERNEL_TOKEN` and/or `AETHER_ODK_TOKEN`; that's going to
be used for all requests and will allow the system to better track the user actions.

*[Return to TOC](#table-of-contents)*


## Development

All development should be tested within the container, but developed in the host folder.
Read the [docker-compose-base.yml](docker-compose-base.yml) file to see how it's mounted.

*[Return to TOC](#table-of-contents)*


## Deployment

Set the `HOSTNAME` and `CAS_SERVER_URL` environment variables if you want to
activate the UMS integration in each container.

Set the `AETHER_KERNEL_TOKEN` and `AETHER_KERNEL_URL` environment variables when
starting the `aether-odk-module` to have ODK Collect submissions posted to Aether Kernel.

If a valid `AETHER_KERNEL_TOKEN` and `AETHER_KERNEL_URL` combination is not set,
the server will still start, but ODK Collect submissions will fail.

To check if it is possible to connect to Aether Kernel with those variables
visit the entrypoint `/check-kernel` in the odk server (no credentials needed).
If the response is `Always Look on the Bright Side of Life!!!`
it's not possible to connect, on the other hand if the message is
`Brought to you by eHealth Africa - good tech for hard places` everything goes fine.

This also applies for `aether-couchdb-sync-module` and `aether-ui`.

In the case of `aether-couchdb-sync-module` a valid `GOOGLE_CLIENT_ID`
environment variable is necessary to verify the device credentials as well.

Infrastructure deployment is done with Terraform, which configuration
files are stored in [terraform](terraform) directory.

Application deployment is managed by AWS Elastic Container Service and is
being done automatically on the following branches/environments:

- branch `develop` is deployed to `dev` environment.
  [![Build Status](https://travis-ci.com/eHealthAfrica/aether.svg?token=Rizk7xZxRNoTexqsQfXy&branch=develop)](https://travis-ci.com/eHealthAfrica/aether)

- branch `master` is deployed to `prod` environment.
  [![Build Status](https://travis-ci.com/eHealthAfrica/aether.svg?token=Rizk7xZxRNoTexqsQfXy&branch=master)](https://travis-ci.com/eHealthAfrica/aether)

*[Return to TOC](#table-of-contents)*


## Containers and services

The list of the main containers:


| Container         | Description                                                             |
| ----------------- | ----------------------------------------------------------------------- |
| db                | [PostgreSQL](https://www.postgresql.org/) database                      |
| couchdb           | [CouchDB](http://couchdb.apache.org/) database for sync                 |
| redis             | [Redis](https://redis.io/) for task queueing and task result storage    |
| **kernel**        | Aether Kernel                                                           |
| **odk**           | Aether ODK module (imports data from ODK Collect)                       |
| **couchdb-sync**  | Aether CouchDB Sync module (imports data from Aether Mobile app)        |
| couchdb-sync-rq   | [RQ python](http://python-rq.org/) task runner to perform sync jobs     |
| kernel-test       | Aether Kernel TESTING app (used only in e2e tests by other containers)  |


All of the containers definition for development can be found in the
[docker-compose-base.yml](docker-compose-base.yml) file.

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

Before running `odk` or `couchdb-sync` you should start the needed test containers.

```bash
docker-compose -f docker-compose-test.yml up -d <container-name>-test
```

This script will start the auxiliary containers and execute the tests
in `odk` or `couchdb-sync`.

```bash
./scripts/test_with_kernel.sh <container-name>
```

**WARNING**

Never run `odk` or `couchdb-sync` tests against any PRODUCTION server.
The tests clean up will **DELETE ALL MAPPINGS!!!**

Look into [docker-compose-base.yml](docker-compose-base.yml), the variable
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
