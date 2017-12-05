# encoding: utf-8
import uuid
from datetime import datetime
from django.contrib.postgres.fields import JSONField
from django.db import models

from .utils import json_prettified

STATUS_CHOICES = (
    ('Pending Approval', 'Pending Approval'),
    ('Publishable', 'Publishable'),
)


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    revision = models.TextField()
    name = models.CharField(max_length=50, db_index=True, unique=True)
    salad_schema = models.TextField()
    jsonld_context = models.TextField()
    rdf_definition = models.TextField()

    def __str__(self):
        return self.name


class Mapping(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, db_index=True, unique=True)
    definition = JSONField(blank=False, null=False)
    revision = models.TextField()
    project = models.ForeignKey(Project, related_name='mappings')

    @property
    def definition_prettified(self):
        return json_prettified(self.definition)

    def __str__(self):
        return self.name


class Submission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    revision = models.TextField(default='1')
    map_revision = models.TextField(default='1')
    date = models.DateTimeField(auto_now_add=True, db_index=True)
    payload = JSONField(blank=False, null=False)
    mapping = models.ForeignKey(Mapping, related_name='submissions', blank=True, null=True)

    @property
    def payload_prettified(self):
        return json_prettified(self.payload)

    def __str__(self):
        return '{} - {}'.format(str(self.mapping), self.id)


class Schema(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, db_index=True, unique=True)
    type = models.CharField(max_length=50)
    definition = JSONField(blank=False, null=False)
    revision = models.TextField()

    @property
    def definition_prettified(self):
        return json_prettified(self.definition)

    def __str__(self):
        return self.name


class ProjectSchema(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, db_index=True, unique=True)
    mandatory_fields = models.CharField(max_length=100)
    transport_rule = models.TextField()
    masked_fields = models.TextField()
    is_encrypted = models.BooleanField(default=False)
    project = models.ForeignKey(Project, related_name='projectschemas')
    schema = models.ForeignKey(Schema, related_name='projectschemas')

    def __str__(self):
        return self.name


class Entity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    revision = models.TextField(default='1')
    payload = JSONField(blank=False, null=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    projectschema = models.ForeignKey(ProjectSchema, related_name='entities')
    submission = models.ForeignKey(Submission, related_name='entities', blank=True, null=True)
    modified = models.CharField(max_length=100, editable=False)

    def save(self, **kwargs):
        if self.modified:
            self.modified = '{}-{}'.format(datetime.now().isoformat(), self.modified[27:None])
        else:
            self.modified = '{}-{}'.format(datetime.now().isoformat(), self.id)
        super(Entity, self).save(**kwargs)

    @property
    def payload_prettified(self):
        return json_prettified(self.payload)

    def __str__(self):
        return 'Entity {}'.format(self.id)

    class Meta:
        verbose_name_plural = 'entities'
