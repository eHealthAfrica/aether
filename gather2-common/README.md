# Gather2 common

This module contains the shared features among different containers.

All the features that can be re-use in other containers and are container
"agnostic" should be moved to this module.

## Sections

### Auth section

Includes the methods that allow:

#### To create "admin" users via command.

```bash
  # arguments: -u=admin -p=secretsecret -e=admin@gather2.org -t=01234656789abcdefghij
  ./manage.py setup_admin -p=$ADMIN_PASSWORD -t=$ADMIN_TOKEN
```


#### To create "users" with auth token via POST request.

Include the view entry in the ``urls.py`` file.

```python
  from django.conf.urls import url
  from gather2.common.auth.views import obtain_auth_token


  urlpatterns = [
      url(r'^get-token', obtain_auth_token, name='token'),
  ]
```


### Core section

Includes the methods that allow:

#### To check connection to Gather2 Core Server.

Include the view entry in the ``urls.py`` file.

```python
  from django.conf.urls import url
  from gather2.common.core.views import check_core


  urlpatterns = [
      url(r'^check-core', check_core, name='check-core'),
  ]
```

#### To make submissions linked to an existing mapping.

```python
  gather2.common.core.utils.submit_to_core(submission, mapping_id, submission_id=None)
```

### Conf section

Import this line to have the common app settings.

```python
  # Common settings
  # ------------------------------------------------------------------------------

  from gather2.common.conf.settings import *  # noqa
```

## How to create the package distribution

Execute the following command in this folder.

```bash
  python setup.py bdist_wheel
```


## How to test the module

To ease the process the tests are run within a docker container.

```bash
  docker-compose -f docker-compose-test.yml run common-test test
```
