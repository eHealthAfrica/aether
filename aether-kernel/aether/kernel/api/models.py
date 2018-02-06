# encoding: utf-8
import uuid
from datetime import datetime
from hashlib import md5
from django.contrib.postgres.fields import JSONField
from django.db import models
from model_utils.models import TimeStampedModel

from .utils import json_prettified

STATUS_CHOICES = (
    ('Pending Approval', 'Pending Approval'),
    ('Publishable', 'Publishable'),
)


'''

Data model schema:


    +------------------+          +------------------+       +------------------+       +---------------------+
    | Project          |          | Mapping          |       | Submission       |       | Attachment          |
    +==================+          +==================+       +==================+       +=====================+
    | id               |<-----+   | id               |<--+   | id               |<--+   | id                  |
    | revision         |      |   | revision         |   |   | revision         |   |   | name                |
    | name             |      |   | name             |   |   | date             |   |   | attachment_file     |
    | salad_schema     |      |   | definition       |   |   | payload          |   |   | md5sum              |
    | jsonld_context   |      |   +::::::::::::::::::+   |   +::::::::::::::::::+   |   +:::::::::::::::::::::+
    | rdf_definition   |      +--<| project          |   +--<| mapping          |   +--<| submission          |
    +------------------+      |   +------------------+       | map_revision     |   |   | submission_revision |
                              |                              +------------------+   |   +---------------------+
                              |                                                     |
    +------------------+      |   +------------------+       +------------------+   |
    | Schema           |      |   | ProjectSchema    |       | Entity           |   |
    +==================+      |   +==================+       +==================+   |
    | id               |<--+  |   | id               |<--+   | id               |   |
    | revision         |   |  |   | name             |   |   | revision         |   |
    | name             |   |  |   | mandatory_fields |   |   | payload          |   |
    | definiton        |   |  |   | transport_rule   |   |   | status           |   |
    | type             |   |  |   | masked_fields    |   |   | modified         |   |
    +------------------+   |  |   | is_encrypted     |   |   +::::::::::::::::::+   |
                           |  |   +::::::::::::::::::+   |   | submission       |>--+
                           |  +--<| project          |   +--<| projectschema    |
                           +-----<| schema           |       +------------------+
                                  +------------------+

'''


class Project(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    _id = models.UUIDField(default=uuid.uuid4, editable=False)
    revision = models.TextField(editable=False)
    name = models.CharField(max_length=50)
    salad_schema = models.TextField()
    jsonld_context = models.TextField()
    rdf_definition = models.TextField()
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'kernel'
        default_related_name = 'projects'
        ordering = ['name', 'revision']

    def save(self, *args, **kwargs):
        if not self.revision:
            self.revision = str(self._id) + '+' + datetime.now().isoformat()
            super(Project, self).save(**kwargs)
        else:
            self.revision = str(self._id) + '+' + datetime.now().isoformat()
            self.id = None
            super(Project, self).save(force_insert=True, force_update=False, *args, **kwargs)


class Mapping(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    _id = models.UUIDField(default=uuid.uuid4, editable=False)
    deleted = models.BooleanField(default=False)
    revision = models.TextField(editable=False)
    name = models.CharField(max_length=50)
    definition = JSONField(blank=False, null=False)
    project = models.ForeignKey(to=Project, on_delete=models.CASCADE)

    @property
    def definition_prettified(self):
        return json_prettified(self.definition)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'kernel'
        default_related_name = 'mappings'
        ordering = ['name', 'revision']

    def save(self, *args, **kwargs):
        if not self.revision:
            self.revision = str(self._id) + '+' + datetime.now().isoformat()
            super(Mapping, self).save(**kwargs)
        else:
            self.revision = str(self._id) + '+' + datetime.now().isoformat()
            self.id = None
            super(Mapping, self).save(force_insert=True, force_update=False, *args, **kwargs)


class Submission(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    _id = models.UUIDField(default=uuid.uuid4, editable=False)
    deleted = models.BooleanField(default=False)
    revision = models.TextField(editable=False)
    map_revision = models.TextField(default='1')
    date = models.DateTimeField(auto_now_add=True, db_index=True)
    payload = JSONField(blank=False, null=False)
    mapping = models.ForeignKey(to=Mapping, related_name='submissions', on_delete=models.CASCADE)

    @property
    def payload_prettified(self):
        return json_prettified(self.payload)

    def __str__(self):
        return '{} - {}'.format(str(self.mapping), self.id)

    class Meta:
        app_label = 'kernel'
        default_related_name = 'submissions'
        ordering = ['mapping', '-date']

    def save(self, *args, **kwargs):
        if not self.revision:
            self.revision = str(self._id) + '+' + datetime.now().isoformat()
            super(Submission, self).save(**kwargs)
        else:
            self.revision = str(self._id) + '+' + datetime.now().isoformat()
            self.id = None
            super(Submission, self).save(force_insert=True, force_update=False, *args, **kwargs)


def __attachment_path__(instance, filename):
    # file will be uploaded to MEDIA_ROOT/<submission_id>/{submission_revision}/filename
    return '{submission}/{revision}/{attachment}'.format(
        submission=instance.submission.id,
        revision=instance.submission_revision,
        attachment=filename,
    )


class Attachment(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    _id = models.UUIDField(default=uuid.uuid4, editable=False)
    deleted = models.BooleanField(default=False)
    revision = models.TextField(editable=False)
    submission = models.ForeignKey(to=Submission, on_delete=models.CASCADE)
    submission_revision = models.TextField()

    # http://www.linfo.org/file_name.html
    # Modern Unix-like systems support long file names, usually up to 255 bytes in length.
    name = models.CharField(max_length=255)
    attachment_file = models.FileField(upload_to=__attachment_path__)
    # save attachment hash to check later if the file is not corrupted
    md5sum = models.CharField(blank=True, max_length=36)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # calculate file hash
        md5hash = md5()
        for chunk in self.attachment_file.chunks():
            md5hash.update(chunk)
        self.md5sum = md5hash.hexdigest()

        # assign current submission revision if missing
        if not self.submission_revision:
            self.submission_revision = self.submission.revision

        # assign name if missing
        if not self.name:
            self.name = self.attachment_file.name

        if not self.revision:
            self.revision = str(self._id) + '+' + datetime.now().isoformat()
            super(Attachment, self).save(**kwargs)
        else:
            self.revision = str(self._id) + '+' + datetime.now().isoformat()
            self.id = None
            super(Attachment, self).save(force_insert=True, force_update=False, *args, **kwargs)

    class Meta:
        app_label = 'kernel'
        default_related_name = 'attachments'
        ordering = ['submission', 'submission_revision', 'name']


class Schema(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    type = models.CharField(max_length=50)
    definition = JSONField(blank=False, null=False)
    _id = models.UUIDField(default=uuid.uuid4, editable=False)
    deleted = models.BooleanField(default=False)
    revision = models.TextField(editable=False)

    @property
    def definition_prettified(self):
        return json_prettified(self.definition)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'kernel'
        default_related_name = 'schemas'
        ordering = ['name', 'revision']

    def save(self, *args, **kwargs):
        if not self.revision:
            self.revision = str(self._id) + '+' + datetime.now().isoformat()
            super(Schema, self).save(force_insert=False, **kwargs)
        else:
            self.revision = str(self._id) + '+' + datetime.now().isoformat()
            self.id = None
            super(Schema, self).save(force_insert=True, force_update=False, *args, **kwargs)


class ProjectSchema(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    _id = models.UUIDField(default=uuid.uuid4, editable=False)
    deleted = models.BooleanField(default=False)
    revision = models.TextField(editable=False)
    name = models.CharField(max_length=50)
    mandatory_fields = models.CharField(max_length=100)
    transport_rule = models.TextField()
    masked_fields = models.TextField()
    is_encrypted = models.BooleanField(default=False)
    project = models.ForeignKey(to=Project, on_delete=models.CASCADE)
    schema = models.ForeignKey(to=Schema, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'kernel'
        default_related_name = 'projectschemas'

    def save(self, *args, **kwargs):
        if not self.revision:
            self.revision = str(self._id) + '+' + datetime.now().isoformat()
            super(ProjectSchema, self).save(**kwargs)
        else:
            self.revision = str(self._id) + '+' + datetime.now().isoformat()
            self.id = None
            super(ProjectSchema, self).save(force_insert=True, force_update=False, *args, **kwargs)


class Entity(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    _id = models.UUIDField(default=uuid.uuid4, editable=False)
    deleted = models.BooleanField(default=False)
    revision = models.TextField(editable=False)
    payload = JSONField(blank=False, null=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    projectschema = models.ForeignKey(to=ProjectSchema, on_delete=models.CASCADE)
    submission = models.ForeignKey(to=Submission, on_delete=models.CASCADE, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.revision:
            self.revision = str(self._id) + '+' + datetime.now().isoformat()
            super(Entity, self).save(**kwargs)
        else:
            self.revision = str(self._id) + '+' + datetime.now().isoformat()
            self.id = None
            super(Entity, self).save(force_insert=True, force_update=False, *args, **kwargs)

    @property
    def payload_prettified(self):
        return json_prettified(self.payload)

    def __str__(self):
        return 'Entity {}'.format(self.id)

    class Meta:
        app_label = 'kernel'
        default_related_name = 'entities'
        verbose_name_plural = 'entities'
