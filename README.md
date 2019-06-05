# Aether

> A free, open source development platform for data curation, exchange, and publication.

## Table of contents

- [Table of contents](#table-of-contents)
- [Setup](#Setup)
  - [Dependencies](#dependencies)
  - [Installation](#installation)
  - [Aether Django SDK Library](#aether-django-sdk-library)
  - [Environment Variables](#environment-variables)
    - [Generic](#generic)
    - [File Storage System](#file-storage-system)
    - [Multi-tenancy](#multi-tenancy)
    - [uWSGI](#uwsgi)
    - [Aether Kernel](#aether-kernel)
    - [Aether ODK Module](#aether-odk-module)
    - [Aether UI](#aether-ui)
    - [Aether CouchDB Sync Module](#aether-couchdb-sync-module)
- [Usage](#usage)
  - [Start the app](#start-the-app)
  - [Users & Authentication](#users--authentication)
    - [Basic Authentication](#basic-authentication)
    - [Token Authentication](#token-authentication)
    - [Gateway Authentication](#gateway-authentication)
- [Development](#development)
- [Release Management](#release-management)
- [Deployment](#deployment)
- [Containers and services](#containers-and-services)
- [Run commands in the containers](#run-commands-in-the-containers)
  - [Run tests](#run-tests)
  - [Upgrade python dependencies](#upgrade-python-dependencies)
    - [Check outdated dependencies](#check-outdated-dependencies)
    - [Update requirements file](#update-requirements-file)
- [Troubleshooting](/TROUBLESHOOTING.md)


## Setup

### Dependencies

- git
- [docker-compose](https://docs.docker.com/compose/)
- [openssl](https://www.openssl.org/) (credentials script)

*[Return to TOC](#table-of-contents)*

### Installation

##### Clone the repository

```bash
git clone git@github.com:eHealthAfrica/aether.git && cd aether
```

##### Generate credentials for local development with docker-compose

**Note:** Make sure you have [openssl](https://www.openssl.org/) installed in your system.

```bash
./scripts/build_docker_credentials.sh > .env
```

##### Build containers and start the applications

```bash
./scripts/build_all_containers.sh && ./scripts/docker_start.sh
```
or

```bash
./scripts/docker_start.sh --build
```

**IMPORTANT NOTE**: the docker-compose files are intended to be used exclusively
for local development. Never deploy these to publicly accessible servers.

##### Include this entry in your `/etc/hosts` or `C:\Windows\System32\Drivers\etc\hosts` file

```text
127.0.0.1    aether.local
```

> Note: `aether.local` is the `NETWORK_DOMAIN` value (see generated `.env` file).

*[Return to TOC](#table-of-contents)*

### Aether Django SDK library

This library contains the shared features among different aether django containers.

See more in its [repository](https://github.com/ehealthafrica/aether-django-sdk-library).

*[Return to TOC](#table-of-contents)*

### Environment Variables

Most of the environment variables are set to default values. This is the short list
of the most common ones with non default values. For more info take a look at the file
[docker-compose-base.yml](docker-compose-base.yml).

Also check the aether sdk section about [environment variables](https://github.com/eHealthAfrica/aether-django-sdk-library#environment-variables).

#### Generic

- `ADMIN_USERNAME`: `admin` The setup scripts create an initial admin user for the app.
- `ADMIN_PASSWORD`: `secresecret`.
- `ADMIN_TOKEN`: `admin_user_auth_token` Used to connect from other modules.
- `WEB_SERVER_PORT` Web server port for the app.

Read [Users & Authentication](#users--authentication) to know the environment
variables that set up the different authentication options.

*[Return to TOC](#table-of-contents)*

#### File Storage System

https://github.com/eHealthAfrica/aether-django-sdk-library#file-storage-system

Used on Kernel and ODK Module

#### Multi-tenancy

https://github.com/eHealthAfrica/aether-django-sdk-library#multi-tenancy

Example with multi-tenancy enabled:

```ini
# .env file
MULTITENANCY=yes
DEFAULT_REALM=my-current-tenant
REALM_COOKIE=cookie-realm
```

```bash
./scripts/docker_start.sh
```

Example with multi-tenancy disabled:

```ini
# .env file
MULTITENANCY=
```

```bash
./scripts/docker_start.sh
```

**Notes:**

- Everything is accessible to admin users in the `admin` section.

- In Aether Kernel:
  - All the schemas are accessible to all tenants.
  - The entities without project are not accessible using the REST API.

- In Aether CouchDB-Sync module:
  - Devices are not restricted by realm but its user account is.

*[Return to TOC](#table-of-contents)*

#### uWSGI

The uWSGI server is responsible for loading our Django applications using
the WSGI interface in production.

We have a couple of environment variables to tune it up:

- `CUSTOM_UWSGI_ENV_FILE` Path to a file of environment variables to use with uWSGI.

- `CUSTOM_UWSGI_SERVE_STATIC` Indicates if uWSGI also serves the static content.
  Is `false` if unset or set to empty string, anything else is considered `true`.

- Any `UWSGI_A_B_C` Translates into the `a-b-c` uswgi option.

  > [
    *When passed as environment variables, options are capitalized and prefixed
    with UWSGI_, and dashes are substituted with underscores.*
  ](https://uwsgi-docs.readthedocs.io/en/latest/Configuration.html#environment-variables)

https://uwsgi-docs.readthedocs.io/

*[Return to TOC](#table-of-contents)*

#### Aether Kernel

The default values for the export feature:

- `EXPORT_CSV_ESCAPE`: `\\`. A one-character string used to escape the separator
  and the quotechar char.
- `EXPORT_CSV_QUOTE`: `"`. A one-character string used to quote fields containing
  special characters, such as the separator or quote char, or which contain
  new-line characters.
- `EXPORT_CSV_SEPARATOR`: `,`. A one-character string used to separate the columns.
- `EXPORT_DATA_FORMAT`: `split`. Indicates how to parse the data into the
  file or files. Values: `flatten`, any other `split`.
- `EXPORT_HEADER_CONTENT`: `labels`. Indicates what to include in the header.
  Options: ``labels`` (default), ``paths``, ``both``.
- `EXPORT_HEADER_SEPARATOR`: `/`. A one-character string used to separate the
  nested columns in the headers row.
- `EXPORT_HEADER_SHORTEN`: `no`. Indicates if the header includes the full
  jsonpath/label or only the column one. Values: ``yes``, any other ``no``.

#### Aether ODK Module

- `AETHER_KERNEL_TOKEN`: `kernel_any_user_auth_token` Token to connect to kernel server.
- `AETHER_KERNEL_TOKEN_TEST`: `kernel_any_user_auth_token` Token to connect to testing kernel server.
- `AETHER_KERNEL_URL`: `http://aether.local/kernel/` Aether Kernel Server url.
- `AETHER_KERNEL_URL_TEST`: `http://kernel-test:9100` Aether Kernel Testing Server url.
- `ODK_COLLECT_ENDPOINT`: the endpoint for all ODK collect urls.
  If it's `collect/` the submission url would be `http://my-server/collect/submission`
  If it's blank ` ` the forms list url would be `http://my-server/formList`

#### Aether UI

- `AETHER_KERNEL_TOKEN`: `kernel_any_user_auth_token` Token to connect to kernel server.
- `AETHER_KERNEL_TOKEN_TEST`: `kernel_any_user_auth_token` Token to connect to testing kernel server.
- `AETHER_KERNEL_URL`: `http://aether.local/kernel/` Aether Kernel Server url.
- `AETHER_KERNEL_URL_TEST`: `http://kernel-test:9100` Aether Kernel Testing Server url.

#### Aether CouchDB Sync Module

- `GOOGLE_CLIENT_ID`: `generate_it_in_your_google_developer_console`
  Token used to verify the device identity with Google.
  See more in https://developers.google.com/identity/protocols/OAuth2
- `AETHER_KERNEL_TOKEN`: `kernel_any_user_auth_token` Token to connect to kernel server.
- `AETHER_KERNEL_TOKEN_TEST`: `kernel_any_user_auth_token` Token to connect to testing kernel server.
- `AETHER_KERNEL_URL`: `http://aether.local/kernel/` Aether Kernel Server url.
- `AETHER_KERNEL_URL_TEST`: `http://kernel-test:9100` Aether Kernel Testing Server url.

## Usage

### Start the app

Start the indicated app/module with the necessary dependencies:

```bash
./scripts/docker_start.sh [options] name
```

Options:

  - `--build` | `-b`   kill and build all containers before start
  - `--clean` | `-c`   stop and remove all running containers and volumes before start
  - `--force` | `-f`   ensure that the container will be restarted if needed
  - `--kill`  | `-k`   kill all running containers before start
  - `name` expected values: `kernel`, `odk`, `ui`, `couchdb-sync` or `sync`
    (alias of `couchdb-sync`).
    Any other value will start all containers.

This will start:

- **Aether UI** on `http://aether.local/`.

- **Aether Kernel** on `http://aether.local/kernel/`.

- **Aether ODK Module** on `http://aether.local/odk/` or `http://aether.local:8443/odk/`.

- **Aether CouchDB Sync Module** on `http://aether.local/sync/`.

If you generated an `.env` file during installation, passwords for all superusers can be found there.

To start any container separately:

```bash
./scripts/docker_start.sh kernel          # starts Aether Kernel app and its dependencies

./scripts/docker_start.sh odk             # starts Aether ODK module and its dependencies

./scripts/docker_start.sh ui              # starts Aether UI and its dependencies

./scripts/docker_start.sh couchdb-sync    # starts Aether CouchDB Sync module and its dependencies
```

*[Return to TOC](#table-of-contents)*

### Users & Authentication

https://github.com/eHealthAfrica/aether-django-sdk-library#users--authentication

The available options depend on each container.

*[Return to TOC](#table-of-contents)*

#### Basic Authentication

The communication between Aether ODK Module and ODK Collect is done via
[basic authentication](http://www.django-rest-framework.org/api-guide/authentication/#basicauthentication).

*[Return to TOC](#table-of-contents)*

#### Token Authentication

The internal communication between the containers is done via
[token authentication](http://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication).

In the case of `aether-odk-module`, `aether-ui` and `aether-couchdb-sync-module`
there is a global token to connect to `aether-kernel` set in the **required**
environment variable `AETHER_KERNEL_TOKEN`. Take in mind that this token
belongs to an active `aether-kernel` user but not necessarily to an admin user.

*[Return to TOC](#table-of-contents)*

#### Gateway Authentication

The `GATEWAY_SERVICE_ID` indicates the gateway service, usually matches the
app/module name like `kernel`, `odk`, `ui`, `sync`.

In this case the app urls can be reached in several ways:

Trying to access the health endpoint `/health`:

- http://kernel:8100/health using the internal url
- http://aether.local/my-realm/kernel/health using the gateway url

The authorization and admin endpoints don't depend on any realm so the final urls
use the public realm.

- http://aether.local/-/odk/accounts/
- http://aether.local/-/kernel/admin/

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

## Release Management

To learn more about the Aether release process, refer to the [release management](https://github.com/eHealthAfrica/aether/wiki/Release-Management) page on the wiki.

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
| keycloak          | [Keycloak](https://www.keycloak.org/) for authentication                |
| nginx             | [NGINX](https://www.nginx.com/) the web server                          |
| **kernel**        | Aether Kernel                                                           |
| **odk**           | Aether ODK module (imports data from ODK Collect)                       |
| **ui**            | Aether Kernel UI (advanced mapping functionality)                       |
| **couchdb-sync**  | Aether CouchDB Sync module (imports data from Aether Mobile app)        |


All of the containers definition for development can be found in the
[docker-compose-base.yml](docker-compose-base.yml) file.

*[Return to TOC](#table-of-contents)*

## Run commands in the containers

Each docker container uses the same script as entrypoint. The `entrypoint.sh`
script offers a range of commands to start services or run commands.
The full list of commands can be seen in the script.

The pattern to run a command is always
``docker-compose run --rm <container-name> <entrypoint-command> <...args>``

*[Return to TOC](#table-of-contents)*

### Run tests

This will stop ALL running containers and execute the containers tests.

```bash
./scripts/test_all.sh
```

or making sure that all the requirements are up to date:

```bash
./scripts/test_travis.sh all
```

To execute tests in just one container:
  - `kernel`
  - `client`
  - `ui`
  - `odk`
  - `couchdb-sync`
  - `producer`
  - `integration`

```bash
./scripts/test_container.sh <container-name>
```

or

```bash
docker-compose run --rm <container-name> test
```

or

```bash
docker-compose run --rm <container-name> test_lint
docker-compose run --rm <container-name> test_coverage
```

The e2e tests are run against different containers, the config file used
for them is [docker-compose-test.yml](docker-compose-test.yml).

Before running `odk`, `ui` or `couchdb-sync` you should start the needed test containers.

```bash
docker-compose -f docker-compose-test.yml up -d <container-name>-test
```

**WARNING**

Never run `odk`, `ui` or `couchdb-sync` tests against any PRODUCTION server.
The tests clean up would **DELETE ALL PROJECTS!!!**

Look into [docker-compose-base.yml](docker-compose-base.yml), the variable
`AETHER_KERNEL_URL_TEST` indicates the Aether Kernel Server used in tests.

The tests are run in parallel, use the `TEST_PARALLEL` environment variable
to indicate the number of concurrent jobs.

*[Return to TOC](#table-of-contents)*

### Upgrade python dependencies

#### Check outdated dependencies

```bash
docker-compose run --rm --no-deps <container-name> eval pip list --outdated
```

#### Update requirements file

```bash
./scripts/upgrade_container.sh [--build] [<container-name>]
```

or

```bash
docker-compose run --rm --no-deps <container-name> pip_freeze
```

*[Return to TOC](#table-of-contents)*
