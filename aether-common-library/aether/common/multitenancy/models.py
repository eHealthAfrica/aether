# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.translation import ugettext as _

from .utils import get_current_realm


class MtInstance(models.Model):
    '''
    Multitenancy model to keep the relation between the instances and the realms.

    :ivar Model  instance: One to one relations with the model class
                           indicated in the setting ``MULTITENANCY_MODEL``.
    :ivar text   realm:    The realm name.
    '''

    instance = models.OneToOneField(
        on_delete=models.CASCADE,
        related_name='mt',
        to=settings.MULTITENANCY_MODEL,
        verbose_name=_('instance'),
    )

    realm = models.TextField(
        verbose_name=_('realm'),
    )

    def __str__(self):
        return str(self.instance)

    class Meta:
        app_label = 'multitenancy'
        ordering = ['instance']
        indexes = [
            models.Index(fields=['realm']),
        ]
        verbose_name = _('instance by realm')
        verbose_name_plural = _('instances by realm')


class MtModelAbstract(models.Model):
    '''
    The ``settings.MULTITENANCY_MODEL`` class must extend this one.
    '''

    def save_mt(self, request):
        '''
        Assigns the instance to the current realm.
        '''

        if not settings.MULTITENANCY:
            return

        # assign to current realm
        realm = get_current_realm(request)
        try:
            self.mt.realm = realm
            self.mt.save()
        except ObjectDoesNotExist:
            MtInstance.objects.create(instance=self, realm=realm)

    def is_accessible(self, realm):
        '''
        Checks if the instance "realm" is the given realm.
        '''

        return settings.MULTITENANCY and self.get_realm() == realm

    def get_realm(self):
        '''
        Returns the instance "realm" or the default one if missing.
        '''

        if not settings.MULTITENANCY:
            return None

        try:
            return self.mt.realm
        except ObjectDoesNotExist:
            return settings.DEFAULT_REALM

    class Meta:
        abstract = True


class MtModelChildAbstract(models.Model):
    '''
    The ``settings.MULTITENANCY_MODEL`` linked classes must extend this one
    and implement the ``get_mt_instance`` method.

    The type of relation could be one to one or one to many but never many to many.
    '''

    def is_accessible(self, realm):
        '''
        Checks if the instance "realm" is the given realm.
        '''

        return self.get_mt_instance().is_accessible(realm)

    def get_realm(self):
        '''
        Returns the instance "realm" or the default one if missing.
        '''

        return self.get_mt_instance().get_realm()

    def get_mt_instance(self):
        '''
        Returns the ``settings.MULTITENANCY_MODEL`` instance linked to this one.
        '''
        raise NotImplementedError

    class Meta:
        abstract = True
