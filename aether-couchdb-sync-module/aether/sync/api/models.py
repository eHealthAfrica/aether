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

import uuid

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils.translation import ugettext as _
from django_prometheus.models import ExportModelOperationsMixin

from aether.common.utils import json_prettified

from .couchdb_helpers import delete_user, generate_db_name


'''
Data model schema:

+------------------+     +------------------+
| Project          |     | Schema           |
+==================+     +==================+
| project_id       |<-+  | id               |
| name             |  |  | name             |
+------------------+  |  | avro_schema      |
                      |  +~~~~~~~~~~~~~~~~~~+
                      |  | kernel_id        |
                      |  +::::::::::::::::::+
                      +-<| project          |
                         +------------------+

+------------------+     +-------------------------+
| MobileUser       |     | DeviceDB                |
+==================+     +=========================+
| id               |<-+  | id                      |
| email            |  |  | device_id               |
+------------------+  |  | last_synced_date        |
                      |  | last_synced_seq         |
                      |  | last_synced_date        |
                      |  | last_synced_log_message |
                      |  +:::::::::::::::::::::::::+
                      +-<| mobileuser              |
                         +-------------------------+

'''


class Project(ExportModelOperationsMixin('couchdbsync_project'), models.Model):
    '''
    Database link of an Aether Kernel Project

    :ivar UUID  project_id:  Aether Kernel project ID (primary key).
    :ivar text  name:        Project name (might match the linked Kernel project name).
    '''

    # This is needed to submit data to kernel
    # (there is a one to one relation)
    project_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        verbose_name=_('project ID'),
        help_text=_('This ID corresponds to an Aether Kernel project ID.'),
    )

    name = models.TextField(null=True, blank=True, default='', verbose_name=_('name'))

    def __str__(self):
        return '{} - {}'.format(str(self.project_id), self.name)

    class Meta:
        app_label = 'sync'
        default_related_name = 'projects'
        ordering = ['name']
        verbose_name = _('project')
        verbose_name_plural = _('projects')


class Schema(ExportModelOperationsMixin('couchdbsync_schema'), models.Model):
    '''
    Keeps the relation between the Aether-mobile App JSON schema and the
    Aether Kernel submissions.

    :ivar integer  id:           ID (primary key).
    :ivar text     name:         Schema name used by Aether-mobile App (**unique**).
    :ivar Project  project:      Project.
    :ivar UUID     kernel_id:    Kernel artefact ID bound to this schema.
    :ivar JSON     avro_schema:  AVRO schema that represents the JSON schema used in the Mobile App.
    '''

    name = models.TextField(unique=True, blank=True, verbose_name=_('name'))

    project = models.ForeignKey(to=Project, on_delete=models.CASCADE, verbose_name=_('project'))

    # This ID is used to submit the Schema Couchdb documents to the linked
    # Aether Kernel artefact.
    # If the Schemas are linked to Mappings it's the mapping id,
    # else if they are linked to Mapping Sets the the mapping set id...
    # This value should be replaced every time the Kernel data model changes or
    # the relation between the App Schema and Kernel Artefact does.
    kernel_id = models.UUIDField(
        default=uuid.uuid4,
        verbose_name=_('Kernel ID'),
        help_text=_('This ID corresponds to an Aether Kernel Artefact ID.'),
    )
    avro_schema = JSONField(verbose_name=_('AVRO schema'), blank=True, default=dict)

    @property
    def avro_schema_prettified(self):
        return json_prettified(self.avro_schema)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.name:
            # try to get it from the AVRO schema
            self.name = self.avro_schema.get('name')
        super(Schema, self).save(*args, **kwargs)

    class Meta:
        app_label = 'sync'
        default_related_name = 'schemas'
        ordering = ['name']
        verbose_name = _('schema')
        verbose_name_plural = _('schemas')


class MobileUser(ExportModelOperationsMixin('couchdbsync_mobileuser'), models.Model):
    '''
    List of granted google user accounts.

    If the device user account is not in this table, the device is not allowed to sync.

    :ivar integer  id:     ID (primary key).
    :ivar text     email:  Validated google user email (**unique**).
    '''

    email = models.EmailField(unique=True, verbose_name=_('e-mail'))

    def __str__(self):
        return self.email

    class Meta:
        app_label = 'sync'
        default_related_name = 'mobileusers'
        ordering = ['email']
        verbose_name = _('mobile user')
        verbose_name_plural = _('mobile users')


class DeviceDB(ExportModelOperationsMixin('couchdbsync_devicedb'), models.Model):
    '''
    Keeps the device and its last successful sync import.

    :ivar integer     id:                       ID (primary key).
    :ivar text        device_id:                Device id generated by Aether-mobile App (**unique**).
    :ivar MobileUser  mobileuser:               Current mobile user.
    :ivar datetime    last_synced_date:         Timestamp of the last successful sync import.
    :ivar text        last_synced_seq:          CouchDB ``last_seq`` value
        of the last successful sync import.
    :ivar text        last_synced_log_message:  Contains information about how many
        records were created/updated during the last successful sync import.
    '''

    device_id = models.TextField(unique=True, verbose_name=_('device ID'))
    mobileuser = models.ForeignKey(
        to=MobileUser,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('mobile user'),
    )

    # used to log the sync execution
    last_synced_date = models.DateTimeField(null=True, verbose_name=_('Last synced: date'))
    last_synced_seq = models.TextField(null=True, default='0', verbose_name=_('Last synced: sequence'))
    last_synced_log_message = models.TextField(null=True, verbose_name=_('Last synced: log message'))

    @property
    def db_name(self):
        '''
        Returns the device's db name.
        '''
        return generate_db_name(self.device_id)

    def __str__(self):
        return self.device_id

    class Meta:
        app_label = 'sync'
        default_related_name = 'devices'
        ordering = ['-last_synced_date']
        verbose_name = _('device')
        verbose_name_plural = _('devices')


@receiver(pre_delete, sender=MobileUser)
def mobile_user_pre_delete(sender, instance, *args, **kwargs):
    '''
    When a Mobile User is deleted, delete the CouchDB users to revoke sync access
    '''

    devices = instance.devices.all()
    for device in devices:
        delete_user(device.device_id)
