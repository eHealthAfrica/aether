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
    - [Aether UI](#aether-ui)
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
docker-compose build && docker-compose up
```

**IMPORTANT NOTE**: the docker-compose files are intended to be used exclusively
for local development. Never deploy these to publicly accessible servers.

##### Include this entry in your `/etc/hosts` file

```
127.0.0.1    kernel.aether.local odk.aether.local ui.aether.local sync.aether.local
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
- `DB_NAME`: `aether` Database name.
- `WEB_SERVER_PORT`: `8000` Web server port.
- `AETHER_KERNEL_TOKEN`: `kernel_admin_user_auth_token`
  to connect to it from other modules. It's used within the start up scripts.

#### Aether ODK Module

- `CAS_SERVER_URL`: `https://ums-dev.ehealthafrica.org` Used by UMS.
- `HOSTNAME`: `odk.aether.local` Used by UMS.
- `DB_NAME`: `odk` Database name.
- `WEB_SERVER_PORT`: `8002` Web server port.
- `AETHER_KERNEL_TOKEN`: `kernel_admin_user_auth_token` Token to connect to kernel server.
- `AETHER_KERNEL_URL`: `http://kernel:8000` Aether Kernel Server url.
- `AETHER_KERNEL_URL_TEST`: `http://kernel-test:9000` Aether Kernel Testing Server url.
- `AETHER_ODK_TOKEN`: `odk_admin_user_auth_token`
  to connect to it from other modules. It's used within the start up scripts.

#### Aether UI

- `CAS_SERVER_URL`: `https://ums-dev.ehealthafrica.org` Used by UMS.
- `HOSTNAME`: `ui.aether.local` Used by UMS.
- `DB_NAME`: `ui` Database name.
- `WEB_SERVER_PORT`: `8004` Web server port.
- `AETHER_KERNEL_TOKEN`: `kernel_admin_user_auth_token` Token to connect to kernel server.
- `AETHER_KERNEL_URL`: `http://kernel:8000` Aether Kernel Server url.
- `AETHER_KERNEL_URL_TEST`: `http://kernel-test:9000` Aether Kernel Testing Server url.

#### Aether CouchDB Sync Module

- `CAS_SERVER_URL`: `https://ums-dev.ehealthafrica.org` Used by UMS.
- `HOSTNAME`: `sync.aether.local` Used by UMS.
- `DB_NAME`: `couchdb-sync` Database name.
- `WEB_SERVER_PORT`: `8006` Web server port.
- `AETHER_KERNEL_TOKEN`: `kernel_admin_user_auth_token` Token to connect to kernel server.
- `AETHER_KERNEL_URL`: `http://kernel:8000` Aether Kernel Server url.
- `AETHER_KERNEL_URL_TEST`: `http://kernel-test:9000` Aether Kernel Testing Server url.
- `GOOGLE_CLIENT_ID`: `generate_it_in_your_google_developer_console`
  Token used to verify the device identity with Google.
  See more in https://developers.google.com/identity/protocols/OAuth2

#### File Storage System (Used on Kernel, ODK and UI Modules)
- `DJANGO_REMOTE_STORAGE` (optionsl): Used to specify a custom [Default file storage system](https://docs.djangoproject.com/en/2.0/ref/settings/#std:setting-DEFAULT_FILE_STORAGE). If not provided, defaults to the [Django default storage](https://docs.djangoproject.com/en/2.0/ref/files/storage/#django.core.files.storage.FileSystemStorage) Available options: S3, . More information [here](https://django-storages.readthedocs.io/en/latest/index.html)
- `REMOTE_STATIC_FILES` (optional): Set to "true" to collect static files to the selected `DJANGO_REMOTE_STORAGE`
- `BUCKET_NAME` (optional): Name of the bucket to use for `DJANGO_REMOTE_STORAGE`. Must be unique on the storage provider. If not provided, it defaults to the `HOSTNAME` value. Bucket is automatically created if does not exist.
- `AWS_ACCESS_KEY_ID`: AWS Access Key to your S3 account. Used when `DJANGO_REMOTE_STORAGE=S3`.
- `AWS_SECRET_ACCESS_KEY`: AWS Secret Access Key to your S3 account. Used when `DJANGO_REMOTE_STORAGE=S3`.

**WARNING**

Never run `odk`, `ui` or `couchdb-sync` tests against any PRODUCTION server.
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

- **Aether ODK Module** on `http://odk.aether.local:8002`
  and create a superuser `admin` with the needed TOKEN.

- **Aether UI** on `http://ui.aether.local:8004`
  and create a superuser `admin`.

- **Aether CouchDB Sync Module** on `http://sync.aether.local:8006`
  and create a superuser `admin`.

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

The app defers part of the users management to
[eHA UMS tool](https://github.com/eHealthAfrica/ums).

Set the `HOSTNAME` and `CAS_SERVER_URL` environment variables if you want to
activate the UMS integration in each container.

#### UMS settings for local development

The project is `aether-all` **Aether Suite**.

The client services are:

  - **Aether Kernel (local)** for `kernel.aether.local`.
  - **Aether ODK (local)**  for `odk.aether.local`.
  - **Aether UI (local)** for `ui.aether.local`.
  - **Aether Sync (local)** for `sync.aether.local`.

Other options are to log in via token, via basic authentication or via the
standard django authentication process in the admin section.
The available options depend on each container.

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
To get started on building solutions on Aether, an [aether-bootstrap](https://github.com/eHealthAfrica/aether-bootstrap) repository has been created to serve as both an example and give you a head start. Visit the [Aether Website](http://aether.ehealthafrica.org) for more information on [Try it for yourself](http://aether.ehealthafrica.org/documentation/try/index.html).

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

This script will start the auxiliary containers and execute the tests
in `odk`, `ui` or `couchdb-sync`.

```bash
./scripts/test_with_kernel.sh <container-name>
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
