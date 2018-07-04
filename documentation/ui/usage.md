---
title: Aether - Basic Usage
permalink: documentation/ui/usage.html
---


# Basic usage of Aether



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
  and create a superuser `admin-kernel` with the needed TOKEN.

- **Aether ODK Module** on `http://odk.aether.local:8443`
  and create a superuser `admin-odk` with the needed TOKEN.

- **Aether CouchDB Sync Module** on `http://sync.aether.local:8666`
  and create a superuser `admin-sync`.


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