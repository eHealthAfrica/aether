# encoding: utf-8

from django.contrib.postgres.fields import JSONField
from django.db import models

from .utils import json_prettified

STATUS_CHOICES = (
    ('Pending Approval', 'Pending Approval'),
    ('Publishable', 'Publishable'),
)


class Project(models.Model):
    revision = models.TextField()
    name = models.CharField(max_length=50, db_index=True, unique=True)
    salad_schema = models.TextField()
    jsonld_context = models.TextField()
    rdf_definition = models.TextField()

    def __str__(self):
        return self.name


class Mapping(models.Model):
    name = models.CharField(max_length=50, db_index=True, unique=True)
    definition = JSONField(blank=False, null=False)
    revision = models.TextField()
    project = models.ForeignKey(Project, related_name='mappings')

    @property
    def definition_prettified(self):
        return json_prettified(self.definition)

    def __str__(self):
        return self.name


class Response(models.Model):
    revision = models.TextField()
    map_revision = models.TextField()
    date = models.DateTimeField(auto_now_add=True, db_index=True)
    payload = JSONField(blank=False, null=False)
    mapping = models.ForeignKey(Mapping, related_name='responses', blank=True, null=True)

    @property
    def payload_prettified(self):
        return json_prettified(self.payload)

    def __str__(self):
        return '{} - {}'.format(str(self.mapping), self.id)


class Schema(models.Model):
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
    # uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    revision = models.TextField(default='1')
    payload = JSONField(blank=False, null=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    projectschema = models.ForeignKey(ProjectSchema, related_name='entities')
    response = models.ForeignKey(Response, related_name='entities', blank=True, null=True)

    @property
    def payload_prettified(self):
        return json_prettified(self.payload)

    def __str__(self):
        return 'Entity {}'.format(self.id)

    class Meta:
        verbose_name_plural = 'entities'
