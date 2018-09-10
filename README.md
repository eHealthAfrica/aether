# Aether

> A free, open source development platform for data curation, exchange, and publication.

## Table of contents

- [Table of contents](#table-of-contents)
- [Setup](#Setup)
  - [Dependencies](#dependencies)
  - [Installation](#installation)
  - [Common Module](#common-module)
  - [Environment Variables](#environment-variables)
    - [Aether Kernel](#aether-kernel)
    - [Aether ODK Module](#aether-odk-module)
    - [Aether UI](#aether-ui)
    - [Aether CouchDB Sync Module](#aether-couchdb-sync-module)
    - [File Storage System](#file-storage-system)
- [Usage](#usage)
  - [Users & Authentication](#users--authentication)
    - [Basic Authentication](#basic-authentication)
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

##### Clone the repository

```bash
git clone git@github.com:eHealthAfrica/aether.git && cd aether
```

##### Generate credentials for local development with docker-compose

**Note:** Make sure you have `openssl` installed in your system.

```bash
./scripts/generate-docker-compose-credentials.sh > .env
```

##### Build containers and start the applications

```bash
./scripts/build_aether_containers.sh && ./scripts/docker_start.sh
```
or

```bash
./scripts/docker_start.sh --build
```

**IMPORTANT NOTE**: the docker-compose files are intended to be used exclusively
for local development. Never deploy these to publicly accessible servers.

##### Include this entry in your `/etc/hosts` file

```text
127.0.0.1    kernel.aether.local odk.aether.local ui.aether.local sync.aether.local
```

*[Return to TOC](#table-of-contents)*

### Common module

This module contains the shared features among different containers.

To create a new version and distribute it:

```bash
./scripts/build_common_and_distribute.sh
```

See more in [README](/aether-common-module/README.md).

*[Return to TOC](#table-of-contents)*

### Environment Variables

Most of the environment variables are set to default values. This is the short list
of the most common ones with non default values. For more info take a look at the file
[docker-compose-base.yml](docker-compose-base.yml).

#### Aether Kernel

- `DB_NAME`: `aether` Database name.
- `WEB_SERVER_PORT`: `8000` Web server port.
- `ADMIN_TOKEN`: `kernel_admin_user_auth_token`
  to connect to it from other modules. It's used within the start up scripts.

#### Aether ODK Module

- `DB_NAME`: `odk` Database name.
- `WEB_SERVER_PORT`: `8002` Web server port.
- `AETHER_KERNEL_TOKEN`: `kernel_admin_user_auth_token` Token to connect to kernel server.
- `AETHER_KERNEL_URL`: `http://kernel:8000` Aether Kernel Server url.
- `AETHER_KERNEL_URL_TEST`: `http://kernel-test:9000` Aether Kernel Testing Server url.
- `AETHER_ODK_TOKEN`: `odk_admin_user_auth_token`
  to connect to it from other modules. It's used within the start up scripts.

#### Aether UI

- `DB_NAME`: `ui` Database name.
- `WEB_SERVER_PORT`: `8004` Web server port.
- `AETHER_KERNEL_TOKEN`: `kernel_admin_user_auth_token` Token to connect to kernel server.
- `AETHER_KERNEL_URL`: `http://kernel:8000` Aether Kernel Server url.
- `AETHER_KERNEL_URL_TEST`: `http://kernel-test:9000` Aether Kernel Testing Server url.

#### Aether CouchDB Sync Module

- `DB_NAME`: `couchdb-sync` Database name.
- `WEB_SERVER_PORT`: `8006` Web server port.
- `AETHER_KERNEL_TOKEN`: `kernel_admin_user_auth_token` Token to connect to kernel server.
- `AETHER_KERNEL_URL`: `http://kernel:8000` Aether Kernel Server url.
- `AETHER_KERNEL_URL_TEST`: `http://kernel-test:9000` Aether Kernel Testing Server url.
- `GOOGLE_CLIENT_ID`: `generate_it_in_your_google_developer_console`
  Token used to verify the device identity with Google.
  See more in https://developers.google.com/identity/protocols/OAuth2

#### File Storage System
(Used on Kernel and ODK Module)

- `DJANGO_STORAGE_BACKEND`: Used to specify a [Default file storage system](https://docs.djangoproject.com/en/1.11/ref/settings/#default-file-storage).
  Available options: `filesystem`, `s3`, `gcs`.
  More information [here](https://django-storages.readthedocs.io/en/latest/index.html).
  Setting `DJANGO_STORAGE_BACKEND` is **mandatory**, even for local development
  (in which case "filesystem" would typically be used).

##### File system (`DJANGO_STORAGE_BACKEND=filesystem`)

- `MEDIA_ROOT`: `/media` the local folder in which all the media assets will be stored.
  The files will be served at `$HOSTNAME/media/<file-name>`.

##### S3 (`DJANGO_STORAGE_BACKEND=s3`)

- `BUCKET_NAME`: Name of the bucket to use on s3 (**mandatory**). Must be unique on s3.
- `AWS_ACCESS_KEY_ID`: AWS Access Key to your s3 account. Used when `DJANGO_STORAGE_BACKEND=s3`.
- `AWS_SECRET_ACCESS_KEY`: AWS Secret Access Key to your s3 account. Used when `DJANGO_STORAGE_BACKEND=s3`.

##### Google Cloud Storage (`DJANGO_STORAGE_BACKEND=gcs`)

- `BUCKET_NAME`: Name of the bucket to use on gcs (**mandatory**).
  Create bucket using [Google Cloud Console](https://console.cloud.google.com/)
  and set appropriate permissions.
- `GS_ACCESS_KEY_ID`: Google Cloud Access Key. Used when `DJANGO_STORAGE_BACKEND=gcs`.
  [How to create Access Keys on Google Cloud Storage](https://cloud.google.com/storage/docs/migrating#keys)
- `GS_SECRET_ACCESS_KEY`: Google Cloud Secret Access Key. Used when `DJANGO_STORAGE_BACKEND=gcs`.
  [How to create Access Keys on Google Cloud Storage](https://cloud.google.com/storage/docs/migrating#keys)


**WARNING**

Never run `odk`, `ui` or `couchdb-sync` tests against any PRODUCTION server.
The tests clean up will **DELETE ALL MAPPINGS!!!**

*[Return to TOC](#table-of-contents)*

## Usage

Start the indicated app/module with the necessary dependencies:

```bash
./scripts/docker_start.sh [--kill | -k] [--build | -b] [--force | -f] <name>
```

Arguments:

  `--kill`  | `-k`  kill all running containers before start

  `--build` | `-b`  kill and build all containers before start

  `--force` | `-f`  ensure that the container will be restarted if it was already running

  `name`
    Expected values: `kernel`, `odk`, `ui`, `couchdb-sync` or `sync`
    (alias of `couchdb-sync`).
    Any other value will start all containers.

This will start:

- **Aether Kernel** on `http://kernel.aether.local`
  and create a superuser `$ADMIN_USERNAME` with the given credentials.

- **Aether ODK Module** on `http://odk.aether.local`
  and create a superuser `$ADMIN_USERNAME` with the given credentials.

- **Aether UI** on `http://ui.aether.local`
  and create a superuser `$ADMIN_USERNAME` with the given credentials.

- **Aether CouchDB Sync Module** on `http://sync.aether.local`
  and create a superuser `$ADMIN_USERNAME` with the given credentials.

If you generated an `.env` file during installation, passwords for all superusers can be found there.

To start any app/module separately:

```bash
./scripts/docker_start.sh kernel          # starts Aether Kernel app and its dependencies

./scripts/docker_start.sh odk             # starts Aether ODK module and its dependencies

./scripts/docker_start.sh ui              # starts Aether UI and its dependencies

./scripts/docker_start.sh couchdb-sync    # starts Aether CouchDB Sync module and its dependencies
```

*[Return to TOC](#table-of-contents)*

### Users & Authentication

Set the `HOSTNAME` and `CAS_SERVER_URL` environment variables if you want to
activate the CAS integration in the app.
See more in [Django CAS client](https://github.com/mingchen/django-cas-ng).

Other options are to log in via token, via basic authentication or via the
standard django authentication process in the admin section.

The available options depend on each container.

*[Return to TOC](#table-of-contents)*

#### Basic Authentication

The communication between Aether ODK Module and ODK Collect is done via basic
authentication.

*[Return to TOC](#table-of-contents)*

#### Token Authentication

The communication between the containers is done via
[token authentication](http://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication).

In the case of `aether-odk-module`, `aether-ui` and `aether-couchdb-sync-module`
there is a global token to connect to `aether-kernel` set in the **required**
environment variable `AETHER_KERNEL_TOKEN`.

*[Return to TOC](#table-of-contents)*

## Development

All development should be tested within the container, but developed in the host folder.
Read the [docker-compose-base.yml](docker-compose-base.yml) file to see how it's mounted.

#### Building on Aether

To get started on building solutions on Aether, an
[aether-bootstrap](https://github.com/eHealthAfrica/aether-bootstrap) repository
has been created to serve as both an example and give you a head start.
Visit the [Aether Website](http://aether.ehealthafrica.org) for more information
on [Try it for yourself](http://aether.ehealthafrica.org/documentation/try/index.html).

*[Return to TOC](#table-of-contents)*

## Deployment

Set the `HOSTNAME` and `CAS_SERVER_URL` environment variables if you want to
activate the CAS integration in each container.

Set the `AETHER_KERNEL_TOKEN` and `AETHER_KERNEL_URL` environment variables when
starting the `aether-odk-module` to have ODK Collect submissions posted to Aether Kernel.

If a valid `AETHER_KERNEL_TOKEN` and `AETHER_KERNEL_URL` combination is not set,
the server will still start, but ODK Collect submissions will fail.

To check if it is possible to connect to Aether Kernel with those variables
visit the entrypoint `/check-kernel` in the odk server (no credentials needed).
If the response is `Always Look on the Bright Side of Life!!!`
it's not possible to connect, on the other hand if the message is
`Brought to you by eHealth Africa - good tech for hard places` everything goes fine.

The environment variable `HOSTNAME` is required when `DJANGO_STORAGE_BACKEND` is set to "filesystem".

This also applies for `aether-ui` and `aether-couchdb-sync-module`.

In the case of `aether-couchdb-sync-module` a valid `GOOGLE_CLIENT_ID`
environment variable is necessary to verify the device credentials as well.

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
| **ui**            | Aether Kernel UI (advanced mapping functionality)                       |
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
./scripts/test_container.sh <container-name>
```

or

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

Before running `odk`, `ui` or `couchdb-sync` you should start the needed test containers.

```bash
docker-compose -f docker-compose-test.yml up -d <container-name>-test
```

**WARNING**

Never run `odk`, `ui` or `couchdb-sync` tests against any PRODUCTION server.
The tests clean up will **DELETE ALL MAPPINGS!!!**

Look into [docker-compose-base.yml](docker-compose-base.yml), the variable
`AETHER_KERNEL_URL_TEST` indicates the Aether Kernel Server used in tests.

*[Return to TOC](#table-of-contents)*

### Upgrade python dependencies

#### Check outdated dependencies

```bash
docker-compose run --no-deps <container-name> eval pip list --outdated
```

#### Update requirements file

```bash
./scripts/upgrade_all.sh
```

This also rebuilds `aether.common` module and distributes it within the containers.
Do not forget to include new containers in the file.

or

```bash
docker-compose run --no-deps <container-name> pip_freeze
```

In this case `aether.common` is not rebuilt.

*[Return to TOC](#table-of-contents)*
