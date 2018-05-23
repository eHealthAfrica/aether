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
# software distributed under the License is distributed on anx
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import uuid

from hashlib import md5

from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.db import models, IntegrityError
from django.utils import timezone

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


class Project(models.Model):
    '''
    Database link of a Aether Kernel Project

    The needed and common data is stored here, like the list of granted surveyors.

    '''

    # This is needed to submit data to kernel
    # (there is a one to one relation)
    project_id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    name = models.TextField(null=True, blank=True, default='')

    # the list of granted surveyors
    surveyors = models.ManyToManyField(to=get_user_model(), blank=True)

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


def __validate_xml_data__(value):
    '''
    Validates xml definition
    '''

    try:
        validate_xform(value)
    except Exception as e:
        raise ValidationError(e)


class XForm(models.Model):
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
    kernel_id = models.UUIDField(blank=True, null=True)

    project = models.ForeignKey(to=Project, on_delete=models.CASCADE)

    description = models.TextField(default='', null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    # the list of granted surveyors
    surveyors = models.ManyToManyField(to=get_user_model(), blank=True)

    # here comes the extracted data from an xForm file
    xml_data = models.TextField(blank=True, validators=[__validate_xml_data__])

    # taken from xml_data
    title = models.TextField(default='', editable=False)
    form_id = models.TextField(default='', editable=False)
    version = models.TextField(default='0', blank=True)
    md5sum = models.CharField(default='', editable=False, max_length=36)
    avro_schema = JSONField(blank=True, null=True, editable=False)

    @property
    def hash(self):
        return 'md5:{}'.format(self.md5sum)

    @property
    def download_url(self):
        '''
        https://bitbucket.org/javarosa/javarosa/wiki/FormListAPI

        Represents the `<downloadUrl/>` entry in the forms list.

        '''

        return '{url}?version={version}'.format(
            url=reverse('xform-get-download', kwargs={'pk': self.pk}),
            version=self.version,
        )

    @property
    def manifest_url(self):
        '''
        https://bitbucket.org/javarosa/javarosa/wiki/FormListAPI

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
            raise IntegrityError({'xml_data': ['This field is required']})

        title, form_id, version = get_xform_data_from_xml(self.xml_data)

        self.title = title
        self.form_id = form_id
        if version:
            # set version from xml data
            self.version = version

        self.update_hash(increase_version=version is None)
        self.avro_schema = parse_xform_to_avro_schema(self.xml_data, default_version=self.version)

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
        return '{} - {}'.format(str(self.title), self.form_id)

    class Meta:
        app_label = 'odk'
        default_related_name = 'xforms'
        ordering = ['title', 'form_id']


def __media_path__(instance, filename):
    # file will be uploaded to MEDIA_ROOT/<project>/<xform>/filename
    return '{project}/{xform}/{filename}'.format(
        project=instance.xform.project.pk,
        xform=instance.xform.pk,
        filename=filename,
    )


class MediaFile(models.Model):
    '''
    Database representation of a media file linked to an XForm

    '''

    xform = models.ForeignKey(to=XForm, on_delete=models.CASCADE)

    name = models.TextField(blank=True)
    media_file = models.FileField(upload_to=__media_path__)
    md5sum = models.CharField(editable=False, max_length=36)

    @property
    def hash(self):
        return 'md5:{}'.format(self.md5sum)

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
        return '{} - {}'.format(str(self.xform), self.name)

    class Meta:
        app_label = 'odk'
        default_related_name = 'media_files'
        ordering = ['xform', 'name']
