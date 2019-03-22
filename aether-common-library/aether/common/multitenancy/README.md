# Multi-tenancy

> A place for everything and everything in its place.

## Definition of multi-tenancy

A *tenant* is a group of users sharing the same view on an application they use.
This view includes the data they access, the configuration, the user management,
particular functionality and related non-functional properties.
Usually the groups are members of different legal entities.
This comes with restrictions (e.g. data security and privacy).

*Multi-tenancy* is an approach to share an application instance between multiple
tenants by providing every tenant a dedicated ”share” of the instance,
which is isolated from other shares with regard to performance and data privacy.
A commonly used analogy for explanation is a living complex where different
parties share some of their resources like heating to reduce costs,
but also love to enjoy their privacy and therefore demand a certain level
of isolation (in particular when it comes to noise).


*Rouven Krebs, Christof Momm and Samuel Kounev*

["Architectural Concerns in Multi-tenant SaaS Applications" (PDF)](https://se2.informatik.uni-wuerzburg.de/pa/uploads/papers/paper-371.pdf).

Read more: [multi-tenancy wikipedia entry](https://en.wikipedia.org/wiki/Multitenancy)


## Technical implementation

The module `aether.common.multitenancy` contains all the relevant code to make
multi-tenancy work.

Check the [tests sample](/tests/fakeapp/) to understand how to use it in the app.

In each module/app `settings.py` file is mandatory to indicate the setting
`MULTITENANCY_MODEL` with the model that supports the multi-tenancy one to one
relation, e.g. `MULTITENANCY_MODEL='my_app.MyModel'`.

### `aether.common.multitenancy.permissions.py`

#### `IsAccessibleByRealm`

An object-level permission class to allow access to objects linked to the
current realm for authenticated users. The current realm value is saved in the
request cookie indicated in `settings.REALM_COOKIE`.

This permission is included in the REST-Framework `DEFAULT_PERMISSION_CLASSES`
list if multi-tenacy is enabled.


### `aether.common.multitenancy.models.py`

#### `MtInstance`

A model class to keep the relation between the objects and the realms.

It has two required fields:

- `instance`: (model) one to one relation with the model class indicated in
  the setting `MULTITENANCY_MODEL`.

- `realm`: (text) a string that identifies the realm/tenant.

#### `MtModelAbstract`

The `settings.MULTITENANCY_MODEL` class must extend this abstract model class.
It includes the necessary methods to check permissions and to add the objects
to the realms.

Defined methods:

- `is_accessible(realm)`, checks if the object "realm" is the given realm.
  This method is the one used by `utils.is_accessible_by_realm(request, obj)`
  to check the object accessibility. If multi-tenancy is not enabled returns `true`.

- `get_realm()`, returns the object linked "realm" or the default one
  (`settings.DEFAULT_REALM`) if missing. If multi-tenancy is not enabled
  returns `None`.

- `add_to_realm(request)` adds the object to the current realm even if it
  already belongs to another one. If multi-tenancy is not enabled does nothing.

```python
class MyModel(MtModelAbstract):

    class Meta:
        app_label = 'my_app'
```

#### `MtModelChildAbstract`

An abstract model class with the methods that any model linked with the
multi-tenancy model must have.

The type of relation could be one to one or one to many but never many to many.

Defined methods:

- `is_accessible(realm)`, checks if the object "realm" is the given realm.

- `get_realm()`, returns the object linked "realm".

- `get_mt_instance()` returns the `settings.MULTITENANCY_MODEL` object linked
  to this one (**needs to be implemented**).

```python
class AnotherModel(MtModelChildAbstract):
    my_model = models.ForeignKey(to=MyModel)

    def get_mt_instance(self):
        return self.my_model

    class Meta:
        app_label = 'my_app'


class EvenAnotherModel(MtModelChildAbstract):
    another_model = models.ForeignKey(to=AnotherModel)

    def get_mt_instance(self):
        return self.another_model.my_model

    class Meta:
        app_label = 'my_app'
```


### `aether.common.multitenancy.serializers.py`

#### `MtModelSerializer`

Extends the Rest-Framework `rest_framework.serializers.ModelSerializer` class and
overrides the `create` method to add the newly created object to the
current realm.

The `settings.MULTITENANCY_MODEL` serializer class must extend this class.

```python
class MyModelSerializer(MtModelSerializer):

    class Meta:
        model = MyModel
```

#### `MtPrimaryKeyRelatedField`

Extends the Rest-Framework `rest_framework.serializers.PrimaryKeyRelatedField`
class and overrides `get_queryset` method to filter the data by the current realm.

Expects a `mt_field` property with the path to the `settings.MULTITENANCY_MODEL`
field, for the `MtModelAbstract` class is `None`, for the rest of classes
concatenates the path of the relation tree to `MtModelAbstract` field with `__`
(double underscore). Defaults to `None`.

This class is useful for two reasons:

- In the REST API browsable view, the HTML select options generated to fulfill
  the field will be restricted to the objects linked to the current realm.
- Most important, the `save` method complains if an object that does not belong
  to the current realm is assigned to this field.

```python
class AnotherModelSerializer(rest_framework.serializers.ModelSerializer):
    my_model = MtPrimaryKeyRelatedField(
        queryset=models.MyModel.objects.all(),
        # mt_field=None,  # already refers to the `MtModelAbstract` field
    )

    class Meta:
        model = AnotherModel


class EvenAnotherModelSerializer(rest_framework.serializers.ModelSerializer):
    another_model = MtPrimaryKeyRelatedField(
        queryset=models.AnotherModel.objects.all(),
        mt_field='my_model',  # path to the `MtModelAbstract` field
    )

    class Meta:
        model = EvenAnotherModel
```

#### `MtUserRelatedField`

Extends the Rest-Framework `rest_framework.serializers.PrimaryKeyRelatedField`
class and overrides `get_queryset` method to filter the users data by the
current realm authorization group.

This class is expected to be used with any users queryset or at least with any
model that has a many to many `groups` field with the authorization group model.

```python
class MyUserModel(django.db.models.Model):
    groups = models.ManyToManyField(to='auth.Group')


class WithUserModel(django.db.models.Model):
    my_user = models.ForeignKey(to=MyUserModel)
    auth_user= models.ForeignKey(to=django.contrib.auth.get_user_model())


class WithUserModelSerializer(rest_framework.serializers.ModelSerializer):
    my_user = MtUserRelatedField(
        queryset=MyUserModel.objects.all(),
    )

    auth_user = MtUserRelatedField(
        queryset=django.contrib.auth.get_user_model().objects.all(),
    )

    class Meta:
        model = WithUserModel
```


### `aether.common.multitenancy.views.py`

#### `MtViewSetMixin`

Defines `get_queryset` method to include filter by realm.

Expects a `mt_field` property with the path to the `settings.MULTITENANCY_MODEL`
field, for the `MtModelAbstract` class is `None`, for the rest of classes
concatenates the path of the relation tree to `MtModelAbstract` field with `__`
(double underscore). Defaults to `None`.

Adds two new methods:
- `get_object_or_404(pk)` raises `NOT_FOUND` error if the object does not exist
  or if it is not accessible by current realm, otherwise returns the object.

- `get_object_or_403(pk)` raises `FORBIDDEN` error if the object exists and is
  not accessible by current realm, otherwise returns the object or `None` if
  it does not exist.

Adds a detail endpoint `/{model}/{pk}/is-accessible` only permitted with `HEAD` method,
returns the following statuses:
  - `404 NOT_FOUND ` if the object does not exist
  - `403 FORBIDDEN`  if the object is not accessible by current realm
  - `204 NO_CONTENT` otherwise

All the model view classes controlled by realms could extend this class.
Otherwise the `get_query_set` method must be overriden to filter the data by
current realm.

```python
class MyModelViewSet(MtViewSetMixin, rest_framework.viewsets.ModelViewSet):
    queryset = MyModel.objects.all()
    serializer_class = MyModelSerializer
    # mt_field = None  # not needed in this case

    @action(detail=True, methods=['post'])
    def manual_creation(self, request, *args, **kwargs):
        # sample of instance creation without using the serializer class
        obj = MyModel.objects.create(
            # extract fields from request.data
        )

        # needs to add the object to the realm manually
        obj.add_to_realm(request)

        return Response(data=self.serializer_class(obj).data, status=201)


class AnotherModelViewSet(MtViewSetMixin, rest_framework.viewsets.ModelViewSet):
    queryset = AnotherModel.objects.all()
    serializer_class = AnotherModelSerializer
    mt_field = 'my_model'  # path to the `MtModelAbstract` field

    @action(detail=True, methods=['patch'])
    def create_or_update(self, request, pk, *args, **kwargs):
        # sample of "create or update" object
        # will respond with 403 status
        # if the object already exists but does not belong to the current realm

        if not self.get_object_or_403(pk=pk):
            return self.create(request, *args, **kwargs)
        else:
            return self.update(request, pk, *args, **kwargs)


class EvenAnotherModelViewSet(MtViewSetMixin, rest_framework.viewsets.ModelViewSet):
    queryset = EvenAnotherModel.objects.all()
    serializer_class = EvenAnotherModelSerializer
    mt_field = 'another_model__my_model'  # path to the `MtModelAbstract` field

    @action(detail=True, methods=['patch'])
    def activate(self, request, pk=None, *args, **kwargs):
        # sample of custom patch endpoint
        # will respond with 404 status
        # if the object does not exists or does not belong to the current realm

        obj = self.get_object_or_404(pk=pk)
        obj.active = True
        obj.save()

        return Response(data=self.serializer_class(obj).data, status=200)
```

#### `MtUserViewSetMixin`

Defines `get_queryset` method to include filter by current realm authorization group.

This class is expected to be used with a subclass of the user model class
or at least with any model that has a many to many `groups` field with
the authorization group model.

```python
class MyUserModelViewSet(MtUserViewSetMixin, rest_framework.viewsets.ReadOnlyModelViewSet):
    queryset = MyUserModel.objects.all()
    serializer_class = MyUserModelSerializer


class UserModelViewSet(MtUserViewSetMixin, rest_framework.viewsets.ReadOnlyModelViewSet):
    queryset = django.contrib.auth.get_user_model().objects.all()
    serializer_class = UserSerializer
```


### `aether.common.multitenancy.utils.py`

A collection of useful methods.

- `get_multitenancy_model()`, returns the `settings.MULTITENANCY_MODEL` class.

- `get_current_realm(request)`, finds the current realm in the session or
  within the request cookies or within the request headers.
  While using the token authentication no session/cookie is included in
  the requests, in this case the realm value is included as an HTTP header,
  i.e., if the `REALM_COOKIE` value is `my-realm` the HTTP header name is `HTTP_MY_REALM`.

- `is_accessible_by_realm(request, obj)`, indicates if the object is
  accessible by the current realm. This method is the one used by
  `IsAccessibleByRealm` permission class to check the object accessibility.

- `filter_by_realm(request, data, mt_field=None)`, includes the realm filter
  in the given data object (Queryset or Manager). This method is the one used by
  `MtPrimaryKeyRelatedField.get_query_set` and `MtViewSetMixin.get_query_set`
  methods to get the list of accessible objects.

- `add_current_realm_in_headers(request, headers={})`, includes the current
  realm in the request headers.

- `add_instance_realm_in_headers(instance, headers={})`, includes the object
  realm in the request headers.

- `get_auth_group(request)`, returns the authorization group that represents
  the current realm.

- `add_user_to_realm(request, user)`, adds the current realm authorization
  group to the given user groups.

- `remove_user_to_realm(request, user)`, removes the current realm authorization
  group from the given user groups.

- `filter_users_by_realm(request, data)`, includes the realm authorization group
  filter in the given data object (Queryset or Manager). This method is the one
  used by `MtUserRelatedField.get_query_set` and `MtUserViewSetMixin.get_query_set`
  methods to get the list of accessible users.
