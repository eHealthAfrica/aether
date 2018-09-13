# Aether common

This module contains the shared features among different aether modules.

All the features that can be re-used in other modules and are not module specific
should be moved to this one.

## Sections

### Auth section

Includes the methods that allow:

#### To create "admin" users via command.

```bash
# arguments: -u=admin -p=secretsecret -e=admin@aether.org -t=01234656789abcdefghij
./manage.py setup_admin -u=$ADMIN_USERNAME -p=$ADMIN_PASSWORD -t=$ADMIN_TOKEN
```

#### To create "users" with auth token via POST request.

Include the view entry in the `urls.py` file.

```python
from django.conf.urls import url
from aether.common.auth.views import obtain_auth_token


urlpatterns = [
    url(r'^get-token$', obtain_auth_token, name='token'),
]
```

### Health section

Includes the methods that allow:

#### To check if the system is up.

Include the view entry in the `urls.py` file.

```python
from django.conf.urls import url
from aether.common.health.views import health, check_db


urlpatterns = [
    url(r'^health$', health, name='health'),        # checks if django responds
    url(r'^check-db$', check_db, name='check-db'),  # checks if the db responds
]
```

#### To check if an URL is reachable via command.

```bash
./manage.py check_url -u=http://my-server/url/to/check
```

### Kernel section

Includes the methods that allow:

#### To check connection to Aether Kernel Server.

Include the view entry in the `urls.py` file.

```python
from django.conf.urls import url
from aether.common.kernel.views import check_kernel


urlpatterns = [
    url(r'^check-kernel$', check_kernel, name='check-kernel'),
]
```

Indicates if the app should have an URL that checks if
Aether Kernel Server is reachable with the provided environment
variables `AETHER_KERNEL_URL` and `AETHER_KERNEL_TOKEN`.

Possible responses:

- `Always Look on the Bright Side of Life!!!` ✘
- `Brought to you by eHealth Africa - good tech for hard places` ✔

#### To make submissions linked to an existing project artefact (mapping).

```python
aether.common.kernel.utils.submit_to_kernel(submission, mapping_id, submission_id=None)
```

### Conf section

#### Settings

Import this snippet in the `settings.py` file to have the common app settings.

```python
from aether.common.conf.settings import *  # noqa
```

#### URLs

Include this snippet in the `urls.py` file to generate default `urlpatterns`
based on the app settings.

```python
from aether.common.conf.urls import generate_urlpatterns


urlpatterns = generate_urlpatterns(token=True, kernel=True) + [
    # app specific urls
]
```

Default URLs included:

  - the `/health` URL. Always responds with `200` status and an empty JSON object `{}`.
  - the `/check-db` URL. Responds with `500` status if the database is not available.
  - the `/admin` section URLs.
  - the `/accounts` URLs, checks if the REST Framework ones, using the templates
    indicated in `LOGIN_TEMPLATE` and `LOGGED_OUT_TEMPLATE` environment variables,
    or the CAS ones.
  - the `debug toolbar` URLs only in DEBUG mode.


Based on `settings`:

  - if `DJANGO_STORAGE_BACKEND` is `filesystem` then:

    - the `/media/<path>` URLs. The endpoint gives protected access
      (only logged in users) to media files.

    - the `/media-basic/<path>` URLs. The endpoint gives protected access
      (only logged in users with basic authentication) to media files.

Based on the arguments:

  - `token`: indicates if the app should be able to create and return
             user tokens via POST request and activates the URL.
             The url endpoint is `/accounts/token`.

  - `kernel`: indicates if the app should have an URL that checks if
              Aether Kernel Server is reachable with the provided environment
              variables `AETHER_KERNEL_URL` and `AETHER_KERNEL_TOKEN`.
              The url endpoint is `/check-kernel`.


## How to create the package distribution

Execute the following command in this folder.

```bash
python setup.py bdist_wheel --universal
```

or to ease the process the build is also run within a docker container.

```bash
docker-compose run common build
```


## How to test the module

To ease the process the tests are run within a docker container.

```bash
docker-compose run common test
```
