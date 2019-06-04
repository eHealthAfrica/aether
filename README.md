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

*[Return to TOC](#table-of-contents)*

### Installation

##### Clone the repository

```bash
git clone git@github.com:eHealthAfrica/aether.git && cd aether
```

##### Generate credentials for local development with docker-compose

**Note:** Make sure you have `openssl` installed in your system.

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

#### Generic

- `ADMIN_USERNAME`: `admin` The setup scripts create an initial admin user for the app.
- `ADMIN_PASSWORD`: `secresecret`.
- `ADMIN_TOKEN`: `admin_user_auth_token` Used to connect from other modules.
- `APP_LINK`: `http://aether.ehealthafrica.org`. The link that appears in the DRF web pages.
- `APP_NAME`: `aether`. The app name displayed in the web pages.
- `APP_URL`, `/`. The app url in the server.
  If host is `http://my-server.org` and the app url is `/my-module`,
  the app enpoints will be accessible at `http://my-server.org/my-module/...`.

  ```nginx
  # one NGINX ini file for all modules
  server {
    listen                    80;
    server_name               localhost;

    location /my-module-1 {
      proxy_pass              http://localhost:8801/my-module-1;
    }

    location /my-module-2 {
      proxy_pass              http://localhost:8802/my-module-2;
    }
  }
  ```

- `DB_NAME` Database name.
- `DEBUG` Enables debug mode. Is `false` if unset or set to empty string,
  anything else is considered `true`.
- `LOGGING_FORMATTER`: `json`. The app messages format.
  Possible values: `verbose` or `json`.
- `LOGGING_LEVEL`: `info` Logging level for app messages.
  https://docs.python.org/3.7/library/logging.html#levels
- `TESTING` Indicates if the app executes under test conditions.
  Is `false` if unset or set to empty string, anything else is considered `true`.
- `STATIC_URL` : provides a base url for the static assets to be served from.
- `WEB_SERVER_PORT` Web server port for the app.

Read [Users & Authentication](#users--authentication) to know the environment
variables that set up the different authentication options.

*[Return to TOC](#table-of-contents)*

#### File Storage System

(Used on Kernel and ODK Module)

- `DJANGO_STORAGE_BACKEND`: Used to specify a [Default file storage system](https://docs.djangoproject.com/en/1.11/ref/settings/#default-file-storage).
  Available options: `minio`, `s3`, `gcs`.
  More information [here](https://django-storages.readthedocs.io/en/latest/index.html).
  Setting `DJANGO_STORAGE_BACKEND` is **mandatory**, even for local development
  (in which case "minio" would typically be used with the `minio` service).

##### Minio (`DJANGO_STORAGE_BACKEND=minio`)

- `BUCKET_NAME`: Name of the bucket that will act as MEDIA folder (**mandatory**).
- `MINIO_STORAGE_ACCESS_KEY`: Minio Access Key.
- `MINIO_STORAGE_SECRET_KEY`: Minio Secret Access Key.
- `MINIO_STORAGE_ENDPOINT`: Minio server url endpoint (without scheme).
- `MINIO_STORAGE_USE_HTTPS`: Whether to use TLS or not. Determines the scheme.
- `MINIO_STORAGE_AUTO_CREATE_MEDIA_BUCKET`: Whether to create the bucket if it does not already exist.
- `MINIO_STORAGE_MEDIA_USE_PRESIGNED`: Determines if the media file URLs should be pre-signed.

See more in https://django-minio-storage.readthedocs.io/en/latest/usage

##### S3 (`DJANGO_STORAGE_BACKEND=s3`)

- `BUCKET_NAME`: Name of the bucket to use on s3 (**mandatory**). Must be unique on s3.
- `AWS_ACCESS_KEY_ID`: AWS Access Key to your s3 account.
- `AWS_SECRET_ACCESS_KEY`: AWS Secret Access Key to your s3 account.

##### Google Cloud Storage (`DJANGO_STORAGE_BACKEND=gcs`)

- `BUCKET_NAME`: Name of the bucket to use on gcs (**mandatory**).
  Create bucket using [Google Cloud Console](https://console.cloud.google.com/)
  and set appropriate permissions.
- `GS_ACCESS_KEY_ID`: Google Cloud Access Key.
  [How to create Access Keys on Google Cloud Storage](https://cloud.google.com/storage/docs/migrating#keys)
- `GS_SECRET_ACCESS_KEY`: Google Cloud Secret Access Key.
  [How to create Access Keys on Google Cloud Storage](https://cloud.google.com/storage/docs/migrating#keys)

*[Return to TOC](#table-of-contents)*

#### Multi-tenancy

- `MULTITENANCY`, Enables or disables the feature, is `false` if unset or set
  to empty string, anything else is considered `true`.
- `DEFAULT_REALM`, `aether` The default realm for artefacts created
  if multi-tenancy is not enabled.
- `REALM_COOKIE`, `aether-realm` The name of the cookie that keeps the current
  tenant id in the request headers.

These variables are included in the `.env` file. Change them to enable or disable
the multi-tenancy feature.

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

The technical implementation is explained in
[Multi-tenancy README](/aether-sdk-library/aether/sdk/multitenancy/README.md).

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

Set the `KEYCLOAK_SERVER_URL` and `KEYCLOAK_CLIENT_ID` environment variables if
you want to use Keycloak as authentication server.
`KEYCLOAK_CLIENT_ID` (defaults to `aether`) is the public client that allows
the aether module to authenticate using the Keycloak REST API.
This client id must be added to all the realms used by the aether module.
The `KEYCLOAK_SERVER_URL` must include all the path till the realm is indicated,
usually until `/auth/realms`.

There are two ways of setting up keycloak:

a) In this case the authentication process happens in the server side without
any further user interaction.
```ini
# .env file
KEYCLOAK_SERVER_URL=http://aether.local/auth/realms
KEYCLOAK_BEHIND_SCENES=true
```

b) In this case the user is redirected to the keycloak server to finish the
sign in step.
```ini
# .env file
KEYCLOAK_SERVER_URL=http://aether.local/auth/realms
KEYCLOAK_BEHIND_SCENES=
```

Execute once the `./scripts/setup_keycloak.sh` script to create the keycloak
database and the default realm+client along with the first user
(find credentials in the `.env` file).

Read more in [Keycloak](https://www.keycloak.org).

**Note**: Multi-tenancy is automatically enabled if the authentication server
is keycloak.

Set the `HOSTNAME` and `CAS_SERVER_URL` environment variables if you want to
activate the CAS integration in the app.
See more in [Django CAS client](https://github.com/mingchen/django-cas-ng).

Other options are to log in via token authentication, via basic authentication
or via the standard django authentication.

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

Set `GATEWAY_SERVICE_ID` to enable gateway authentication with keycloak.
This means that the authentication is handled by a third party system
(like [Kong](https://konghq.com)) that includes in each request the JSON Web
Token (JWT) in the `GATEWAY_HEADER_TOKEN` header (defaults to `X-Oauth-Token`).
The `GATEWAY_SERVICE_ID` indicates the gateway service, usually matches the
app/module name like `kernel`, `odk`, `ui`, `sync`.

In this case the app urls can be reached in several ways:

Trying to access the health endpoint `/health`:

- http://kernel:8100/health using the internal url
- http://aether.local/my-realm/kernel/health using the gateway url

For those endpoints that don't depend on the realm and must also be available
"unprotected" we need one more environment variable:

- `GATEWAY_PUBLIC_REALM`: `-` This represents the fake realm that is not protected
  by the gateway server. In this case the authentication is handled by the other
  available options, i.e., basic, token, CAS...

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
