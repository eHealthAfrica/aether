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

from hashlib import md5

from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db import models, IntegrityError
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext as _
from django_prometheus.models import ExportModelOperationsMixin

from aether.common.utils import resolve_file_url

from .xform_utils import (
    get_xform_data_from_xml,
    parse_xform_to_avro_schema,
    validate_xform,
)


'''

Data model schema:


    +------------------+       +-------------------+       +------------------+
    | Project          |       | XForm             |       | MediaFile        |
    +==================+       +===================+       +==================+
    | project_id       |<--+   | id                |<--+   | id               |
    | name             |   |   | xml_data          |   |   | name             |
    +::::::::::::::::::+   |   | description       |   |   | media_file       |
    | surveyors (User) |   |   | created_at        |   |   +~~~~~~~~~~~~~~~~~~+
    +------------------+   |   +~~~~~~~~~~~~~~~~~~-+   |   | md5sum           |
                           |   | title             |   |   +::::::::::::::::::+
                           |   | form_id           |   +--<| xform            |
                           |   | version           |       +------------------+
                           |   | md5sum            |
                           |   | avro_schema       |
                           |   +:::::::::::::::::::+
                           |   | kernel_id         |
                           |   +:::::::::::::::::::+
                           +--<| project           |
                               | surveyors (User)  |
                               +-------------------+

'''


class Project(ExportModelOperationsMixin('odk_project'), models.Model):
    '''
    Database link of an Aether Kernel Project

    The needed and common data is stored here, like the list of granted surveyors.
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

    # the list of granted surveyors
    surveyors = models.ManyToManyField(
        to=get_user_model(),
        blank=True,
        verbose_name=_('surveyors'),
        help_text=_('If you do not specify any surveyors, EVERYONE will be able to access this project xForms.'),
    )

    def is_surveyor(self, user):
        '''
        Indicates if the given user is a granted surveyor of the Project.

        Rules:
            - User is superuser.
            - Project has no surveyors.
            - User is in the surveyors list.

        '''

        return (
            user.is_superuser or
            self.surveyors.count() == 0 or
            user in self.surveyors.all()
        )

    def __str__(self):
        return '{} - {}'.format(str(self.project_id), self.name)

    class Meta:
        app_label = 'odk'
        default_related_name = 'projects'
        ordering = ['name']
        verbose_name = _('project')
        verbose_name_plural = _('projects')


def __validate_xml_data__(value):
    '''
    Validates xml definition
    '''

    try:
        validate_xform(value)
    except Exception as e:
        raise ValidationError(e)


class XForm(ExportModelOperationsMixin('odk_xform'), models.Model):
    '''
    Database representation of an XForm.

    The data is stored in XML format and could be converted to the
    other supported formats when it is needed.


    One XForm should create in Kernel:
        - one Mapping,
        - one Schema and
        - one ProjectSchema.

    '''

    # This is needed to submit data to kernel
    kernel_id = models.UUIDField(
        default=uuid.uuid4,
        verbose_name=_('Aether Kernel ID'),
        help_text=_('This ID is used to create Aether Kernel artefacts (schema, project schema and mapping).'),
    )

    project = models.ForeignKey(to=Project, on_delete=models.CASCADE, verbose_name=_('project'))

    description = models.TextField(default='', null=True, blank=True, verbose_name=_('xForm description'))
    created_at = models.DateTimeField(default=timezone.now, editable=False, verbose_name=_('created at'))
    modified_at = models.DateTimeField(default=timezone.now, verbose_name=_('modified at'))

    # the list of granted surveyors
    surveyors = models.ManyToManyField(
        to=get_user_model(),
        blank=True,
        verbose_name=_('surveyors'),
        help_text=_('If you do not specify any surveyors, EVERYONE will be able to access this xForm.'),
    )

    # here comes the extracted data from an xForm file
    xml_data = models.TextField(
        blank=True,
        validators=[__validate_xml_data__],
        verbose_name=_('XML definition'),
        help_text=_(
            'This XML must conform the ODK XForms specification. '
            'http://opendatakit.github.io/xforms-spec/'
        )
    )

    # taken from xml_data
    title = models.TextField(default='', editable=False, verbose_name=_('xForm title'))
    form_id = models.TextField(default='', editable=False, verbose_name=_('xForm ID'))
    version = models.TextField(default='0', blank=True, verbose_name=_('xForm version'))
    md5sum = models.CharField(default='', editable=False, max_length=36, verbose_name=_('xForm md5sum'))
    avro_schema = JSONField(null=True, blank=True, editable=False, verbose_name=_('AVRO schema'))

    @property
    def hash(self):
        return 'md5:{}'.format(self.md5sum)

    @property
    def download_url(self):
        '''
        https://docs.opendatakit.org/openrosa-form-list/

        Represents the `<downloadUrl/>` entry in the forms list.

        '''

        return '{url}?version={version}'.format(
            url=reverse('xform-get-download', kwargs={'pk': self.pk}),
            version=self.version,
        )

    @property
    def manifest_url(self):
        '''
        https://docs.opendatakit.org/openrosa-form-list/

        Represents the `<manifestUrl/>` entry in the forms list.

        '''

        if self.media_files.count() > 0:
            return '{url}?version={version}'.format(
                url=reverse('xform-get-manifest', kwargs={'pk': self.pk}),
                version=self.version,
            )
        else:
            return ''

    def save(self, *args, **kwargs):
        try:
            self.full_clean()
        except ValidationError as ve:
            raise IntegrityError(ve)

        if not self.xml_data:
            raise IntegrityError({'xml_data': [_('This field is required.')]})

        title, form_id, version = get_xform_data_from_xml(self.xml_data)

        self.title = title
        self.form_id = form_id
        if version:
            # set version from xml data
            self.version = version

        self.update_hash(increase_version=version is None)

        new_avro_schema = parse_xform_to_avro_schema(self.xml_data, default_version=self.version)
        if new_avro_schema != self.avro_schema:
            self.avro_schema = new_avro_schema
            # set a new `kernel_id` value, this will generate
            # a new schema and mapping entry in kernel and
            # new submissions will be assigned to the new one, not the old one.
            # With this we will hopefully keep track of all xform versions
            self.kernel_id = uuid.uuid4()

        # update "modified_at"
        self.modified_at = timezone.now()
        return super(XForm, self).save(*args, **kwargs)

    def is_surveyor(self, user):
        '''
        Indicates if the given user is a granted surveyor of the xForm.

        Rules:
            - User is superuser.
            - xForm and Project have no surveyors.
            - User is in the xForm or Project surveyors list.

        '''

        return (
            user.is_superuser or
            (self.surveyors.count() == 0 and self.project.surveyors.count() == 0) or
            user in self.surveyors.all() or
            user in self.project.surveyors.all()
        )

    def update_hash(self, increase_version=False):
        md5sum = md5(self.xml_data.encode('utf8')).hexdigest()
        if md5sum != self.md5sum and increase_version:
            self.increase_version()
        self.md5sum = md5sum

    def increase_version(self):
        self.version = '{:%Y%m%d%H}'.format(timezone.now())

    def __str__(self):
        return '{} - {}'.format(self.title, self.form_id)

    class Meta:
        app_label = 'odk'
        default_related_name = 'xforms'
        ordering = ['title', 'form_id', 'version']
        verbose_name = _('xform')
        verbose_name_plural = _('xforms')


def __media_path__(instance, filename):
    # file will be uploaded to MEDIA_ROOT/<project>/<xform>/filename
    return '{project}/{xform}/{filename}'.format(
        project=instance.xform.project.pk,
        xform=instance.xform.pk,
        filename=filename,
    )


class MediaFile(ExportModelOperationsMixin('odk_mediafile'), models.Model):
    '''
    Database representation of a media file linked to an XForm
    '''

    xform = models.ForeignKey(to=XForm, on_delete=models.CASCADE, verbose_name=_('xForm'))

    name = models.TextField(blank=True, verbose_name=_('name'))
    media_file = models.FileField(upload_to=__media_path__, verbose_name=_('file'))
    md5sum = models.CharField(editable=False, max_length=36, verbose_name=_('md5sum'))

    @property
    def hash(self):
        return 'md5:{}'.format(self.md5sum)

    @property
    def media_file_url(self):
        return resolve_file_url(self.media_file.url)

    def save(self, *args, **kwargs):
        # calculate hash
        md5hash = md5()
        for chunk in self.media_file.chunks():
            md5hash.update(chunk)
        self.md5sum = md5hash.hexdigest()

        # assign name if missing
        if not self.name:
            self.name = self.media_file.name

        super(MediaFile, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'odk'
        default_related_name = 'media_files'
        ordering = ['xform', 'name']
        verbose_name = _('media file')
        verbose_name_plural = _('media files')
