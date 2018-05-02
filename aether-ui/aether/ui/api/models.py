import requests
import uuid

from collections import namedtuple
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.db import models
from model_utils.models import TimeStampedModel

from ..settings import AETHER_APPS
from .utils import validate_pipeline


'''
Named tuple to pass together the app base url and the user auth token
'''
UserAppToken = namedtuple('UserAppToken', ['base_url', 'token'])


class UserTokens(models.Model):
    '''
    User auth tokens to connect to the different apps.
    '''

    user = models.OneToOneField(to=get_user_model(), primary_key=True, on_delete=models.CASCADE)

    kernel_token = models.CharField(max_length=40, null=True, blank=True)

    def get_app_url(self, app_name):
        '''
        Gets the `url` of the app.
        '''

        if app_name in AETHER_APPS:
            return AETHER_APPS[app_name]['url']

        return None

    def save_app_token(self, app_name, token):
        '''
        Saves the auth `token` of the app.
        '''

        if app_name not in AETHER_APPS:
            return

        app_property = '{}_token'.format(self.__clean_app_name__(app_name))
        setattr(self, app_property, token)
        self.save()

    def get_app_token(self, app_name):
        '''
        Gets the auth `token` of the app.
        '''

        if app_name not in AETHER_APPS:
            return None

        app_property = '{}_token'.format(self.__clean_app_name__(app_name))
        return getattr(self, app_property)

    def create_app_token(self, app_name):
        '''
        Creates a new auth `token` of the app.
        '''

        if app_name not in AETHER_APPS:
            return None

        # obtain it from app server
        token = self.obtain_app_token(app_name)
        self.save_app_token(app_name, token)
        return self.get_app_token(app_name)

    def get_or_create_app_token(self, app_name):
        '''
        Gets the auth `token` of the app. If it does not exist yet, it's created.
        '''

        if app_name not in AETHER_APPS:
            return None

        token = self.get_app_token(app_name)
        if token is None:
            token = self.create_app_token(app_name)
        return token

    def obtain_app_token(self, app_name):
        '''
        Gets the auth `token` of the app from the app itself.
        '''

        if app_name not in AETHER_APPS:
            return None
        base_url = self.get_app_url(app_name)
        auxiliary_token = AETHER_APPS[app_name]['token']

        response = requests.post(
            '{}/accounts/token'.format(base_url),
            data={'username': self.user.username},
            headers={'Authorization': 'Token {token}'.format(token=auxiliary_token)},
        )

        if response.status_code == 200:
            return response.json()['token']

        return None

    def validates_app_token(self, app_name):
        '''
        Checks if with the current auth `token` it's possible to connect to the app server.
        '''

        if app_name not in AETHER_APPS:
            return False
        base_url = self.get_app_url(app_name)
        token = self.get_app_token(app_name)
        if token is None:
            return False

        response = requests.get(
            base_url,
            headers={'Authorization': 'Token {token}'.format(token=token)},
        )
        return response.status_code == 200

    def __clean_app_name__(self, app_name):
        return app_name.replace('-', '_')

    @classmethod
    def get_or_create_user_app_token(cls, user, app_name):
        '''
        Gets the user auth token to connect to the app, checking first if it's valid.
        '''

        if app_name not in AETHER_APPS:
            return None

        user_tokens, _ = cls.objects.get_or_create(user=user)
        base_url = user_tokens.get_app_url(app_name)

        # if the current auth token is not valid then obtain a new one from app server
        if not user_tokens.validates_app_token(app_name):
            token = user_tokens.create_app_token(app_name)
        else:
            token = user_tokens.get_app_token(app_name)

        if token is None:
            return None

        return UserAppToken(base_url=base_url, token=token)

    class Meta:
        app_label = 'ui'
        default_related_name = 'app_tokens'


class Pipeline(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, null=False, blank=False, unique=True)

    # this is the avro schema
    schema = JSONField(blank=True, null=True, default={})

    # this is an example of the data using the avro schema
    input = JSONField(blank=True, null=True, default={})

    # the list of available entity types (avro schemas)
    entity_types = JSONField(blank=True, null=True, default=[])

    # this represents the list of mapping rules
    # {
    #    "mapping": [
    #      {'id': ###, 'source': 'jsonpath-input-1', 'destination: 'jsonpath-entity-type-1'},
    #      {'id': ###, 'source': 'jsonpath-input-2', 'destination: 'jsonpath-entity-type-2'},
    #      ...
    #      {'id': ###, 'source': 'jsonpath-input-n', 'destination: 'jsonpath-entity-type-n'},
    #    ]
    # }
    mapping = JSONField(blank=True, null=True, default=[])

    # these represent the list of entities and errors returned by the
    # `validate-mapping` endpoint in kernel.
    # {
    #    "entities": [
    #      {...},
    #      {...},
    #    ],
    #    "mapping_errors": [
    #      {"path": 'jsonpath-input-a', "error_message": 'No match for path'},
    #      {"path": 'jsonpath-entity-type-b', "error_message": 'No match for path'},
    #      ...
    #    ]
    # }
    mapping_errors = JSONField(blank=True, null=True, editable=False)
    output = JSONField(blank=True, null=True, editable=False)
    kernel_refs = JSONField(blank=True, null=True, editable=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        errors, output = validate_pipeline(self)
        self.mapping_errors = errors
        self.output = output

        super(Pipeline, self).save(*args, **kwargs)

    class Meta:
        app_label = 'ui'
        default_related_name = 'pipelines'
        ordering = ('name',)
