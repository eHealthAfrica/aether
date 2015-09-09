from django.db import models
from django.contrib.postgres.fields import JSONField
import uuid


class Survey(models.Model):
    name = models.CharField(max_length=15)
    schema = JSONField(default=dict, blank=False, null=False)


class SurveyItem(models.Model):
    uuid = models.UUIDField(blank=False, editable=False, default=uuid.uuid4)
    survey = models.ForeignKey(Survey)
    data = JSONField(default={})
