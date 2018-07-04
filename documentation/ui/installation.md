---
title: Aether - Installation
permalink: documentation/ui/installation.html
---


# Installation of Aether



## Setup

### Dependencies

- git
- [docker-compose](https://docs.docker.com/compose/)


### Installation

```bash
git clone git@github.com:eHealthAfrica/aether.git
cd aether

docker-compose build
```

Include this entry in your `/etc/hosts` file:

```
127.0.0.1    kernel.aether.local odk.aether.local sync.aether.local
```

### Common module

This module contains the shared features among different containers.

To create a new version and distribute it:

```bash
./scripts/build_common_and_distribute.sh
```

See more in [README](/aether-common/README.md).


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
