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
./manage.py setup_admin -p=$ADMIN_PASSWORD -t=$ADMIN_TOKEN
```


#### To create "users" with auth token via POST request.

Include the view entry in the `urls.py` file.

- Django 1.x

  ```python
  from django.conf.urls import url
  from aether.common.auth.views import obtain_auth_token


  urlpatterns = [
      url(r'^get-token$', obtain_auth_token, name='token'),
  ]
  ```

- Django 2.x

  ```python
  from django.urls import path
  from aether.common.auth.views import obtain_auth_token


  urlpatterns = [
      path('get-token', obtain_auth_token, name='token'),
  ]
  ```

- Compatibility with both Django 1.x and Django 2.x

  ```python
  from aether.common.conf.urls import url_pattern
  from aether.common.auth.views import obtain_auth_token


  urlpatterns = [
      url_pattern(r'^get-token$', obtain_auth_token, name='token'),
  ]
  ```

### Health section

Includes the methods that allow:

#### To check if the system is up.

Include the view entry in the `urls.py` file.

- Django 1.x

  ```python
  from django.conf.urls import url
  from aether.common.health.views import health


  urlpatterns = [
      url(r'^health$', health, name='health'),
  ]
  ```

- Django 2.x

  ```python
  from django.urls import path
  from aether.common.health.views import health


  urlpatterns = [
      path('health', health, name='health'),
  ]
  ```

- Compatibility with both Django 1.x and Django 2.x

  ```python
  from aether.common.conf.urls import url_pattern
  from aether.common.health.views import health


  urlpatterns = [
      url_pattern(r'^health$', health, name='health'),
  ]
  ```

### Kernel section

Includes the methods that allow:

#### To check connection to Aether Kernel Server.

Include the view entry in the `urls.py` file.

- Django 1.x

  ```python
  from django.conf.urls import url
  from aether.common.kernel.views import check_kernel


  urlpatterns = [
      url(r'^check-kernel$', check_kernel, name='check-kernel'),
  ]
  ```

- Django 2.x

  ```python
  from django.urls import path
  from aether.common.kernel.views import check_kernel


  urlpatterns = [
      path('check-kernel', check_kernel, name='check-kernel'),
  ]
  ```

- Compatibility with both Django 1.x and Django 2.x

  ```python
  from aether.common.conf.urls import url_pattern
  from aether.common.kernel.views import check_kernel


  urlpatterns = [
      url_pattern(r'^check_kernel$', check_kernel, name='check_kernel'),
  ]
  ```

Indicates if the app should have an URL that checks if
Aether Kernel Server is reachable with the provided environment
variables `AETHER_KERNEL_URL` and `AETHER_KERNEL_TOKEN`.

Possible responses:

- `Always Look on the Bright Side of Life!!!` ✘
- `Brought to you by eHealth Africa - good tech for hard places` ✔

#### To make submissions linked to an existing mapping.

```python
aether.common.kernel.utils.submit_to_kernel(submission, mapping_id, submission_id=None)
```

### Conf section

#### Settings

Import this snippet in the `settings.py` file to have the common app settings.

```python
# Common settings
# ------------------------------------------------------------------------------

from aether.common.conf.settings import *  # noqa
```

#### URLs

Provides two methods `url_pattern` and `include` that support Django 1.x and Django 2.x.

```python
from aether.common.conf.urls import include, url_pattern


urlpatterns = [
    url_pattern(r'^my-path', include('aether.my_module.urls', namespace='my-module')),
]
```

Equivalent in Django 1.x to:

    ```python
    from django.conf.urls import include, url


    urlpatterns = [
        url(r'^my-path', include('aether.my_module.urls', namespace='my-module')),
    ]
    ```

Equivalent in Django 2.x to:

    ```python
    from django.urls import include, re_path


    urlpatterns = [
        re_path(r'^my-path', include('aether.my_module.urls', namespace='my-module')),
    ]
    ```


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
  - the `/admin` section URLs.
  - the `/accounts` URLs, checks if the REST Framework ones or the UMS ones.
  - the `debug toolbar` URLs only in DEBUG mode.
  - the `/media` URLS. The endpoint gives protected access (only to logged in users) to media files.
  - the `/media-basic` URLS. The endpoint gives protected access
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


## How to test the module

To ease the process the tests are run within a docker container.

```bash
# checks django 1.x compatibility
docker-compose -f docker-compose-common.yml run common-test-django-1 test

# checks django 2.x compatibility
docker-compose -f docker-compose-common.yml run common-test-django-2 test
```
