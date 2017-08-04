# encoding: utf-8

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models

from .utils import json_prettified, code_prettified

UserModel = settings.AUTH_USER_MODEL


class Survey(models.Model):
    name = models.CharField(max_length=50)
    schema = JSONField(blank=True, null=False, default='{}')
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    created_by = models.ForeignKey(UserModel, db_index=True, related_name='surveys')

    @property
    def schema_prettified(self):
        return json_prettified(self.schema)

    def __str__(self):
        return self.name


class Response(models.Model):
    survey = models.ForeignKey(Survey, related_name='responses')

    data = JSONField(blank=False, null=False)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    created_by = models.ForeignKey(UserModel, db_index=True, related_name='responses')

    @property
    def data_prettified(self):
        return json_prettified(self.data)

    def __str__(self):
        return '{} - {}'.format(str(self.survey), self.id)


class Attachment(models.Model):
    response = models.ForeignKey(Response, related_name='attachments')

    name = models.CharField(max_length=50)
    attachment_file = models.FileField(verbose_name='attachment')
    created = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):  # pragma: no cover
        return '{} - {}'.format(str(self.response), self.name)


class MapFunction(models.Model):
    survey = models.ForeignKey(Survey, related_name='map_functions')

    code = models.TextField()
    created = models.DateTimeField(auto_now_add=True, db_index=True)

    @property
    def code_prettified(self):
        return code_prettified(self.code)

    def __str__(self):
        return '{} - {}'.format(str(self.survey), self.id)


class MapResult(models.Model):
    response = models.ForeignKey(Response, related_name='map_results')
    map_function = models.ForeignKey(MapFunction, related_name='map_results')

    output = JSONField(blank=True, null=False, default='{}', editable=False)
    error = models.TextField(editable=False)
    created = models.DateTimeField(auto_now_add=True, db_index=True)

    @property
    def output_prettified(self):
        return json_prettified(self.output)

    def __str__(self):
        return '{} - {}'.format(str(self.response), self.id)


class ReduceFunction(models.Model):
    map_function = models.ForeignKey(MapFunction, related_name='reduce_functions')

    code = models.TextField()
    output = JSONField(blank=False, null=False, default='{}', editable=False)
    error = models.TextField(blank=True, default='', editable=False)
    created = models.DateTimeField(auto_now_add=True, db_index=True)

    @property
    def code_prettified(self):
        return code_prettified(self.code)

    @property
    def output_prettified(self):
        return json_prettified(self.output)

    def __str__(self):
        return '{} - {}'.format(str(self.map_function), self.id)
