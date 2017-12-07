from collections import namedtuple

from django.contrib.auth import get_user_model
from django.db import models

import requests

from .settings import (
    AETHER_KERNEL_URL,
    AETHER_KERNEL_TOKEN,
    AETHER_ODK,
    AETHER_ODK_URL,
    AETHER_ODK_TOKEN,
)

'''
Current external apps
'''
# only the ones with url and token
AETHER_APPS = []
if AETHER_KERNEL_URL is not None and AETHER_KERNEL_TOKEN is not None:  # pragma: no cover
    AETHER_APPS.append('kernel')

if AETHER_ODK and AETHER_ODK_URL is not None and AETHER_ODK_TOKEN is not None:  # pragma: no cover
    AETHER_APPS.append('odk-importer')

'''
Named tuple to pass together the app base url and the user auth token
'''
UserAppToken = namedtuple('UserAppToken', ['base_url', 'token'])


class UserTokens(models.Model):
    '''
    User auth tokens to connect to the different apps.
    '''

    user = models.OneToOneField(
        to=get_user_model(),
        related_name='app_tokens',
        primary_key=True,
        on_delete=models.CASCADE,
    )

    kernel_token = models.CharField(max_length=40, null=True, blank=True)
    odk_importer_token = models.CharField(max_length=40, null=True, blank=True)
    couchdb_sync_token = models.CharField(max_length=40, null=True, blank=True)

    def get_app_url(self, app_name):
        '''
        Gets the `url` of the app.
        '''

        if app_name == 'kernel':
            return AETHER_KERNEL_URL
        if app_name == 'odk-importer':
            return AETHER_ODK_URL
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
        if base_url is None:
            return None

        auxiliary_token = None
        if app_name == 'kernel':
            auxiliary_token = AETHER_KERNEL_TOKEN
        if app_name == 'odk-importer':
            auxiliary_token = AETHER_ODK_TOKEN
        if auxiliary_token is None:
            return None

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
        if base_url is None:
            return False
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


def get_or_create_valid_app_token(user, app_name):
    '''
    Gets the user auth token to connect to the app, checking first if it's valid.
    '''

    if app_name not in AETHER_APPS:
        return None

    user_tokens, _ = UserTokens.objects.get_or_create(user=user)

    base_url = user_tokens.get_app_url(app_name)
    if base_url is None:
        return None

    # if the current auth token is not valid then obtain a new one from app server
    if not user_tokens.validates_app_token(app_name):
        token = user_tokens.create_app_token(app_name)
    else:
        token = user_tokens.get_app_token(app_name)

    if token is None:
        return None

    return UserAppToken(base_url=base_url, token=token)
