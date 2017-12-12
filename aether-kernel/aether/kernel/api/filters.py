import django_filters.rest_framework as filters

from . import models


class ProjectFilter(filters.FilterSet):
    class Meta:
        fields = '__all__'
        model = models.Project


class MappingFilter(filters.FilterSet):
    class Meta:
        exclude = ('definition',)
        model = models.Mapping


class SubmissionFilter(filters.FilterSet):
    class Meta:
        exclude = ('payload',)
        model = models.Submission


class SchemaFilter(filters.FilterSet):
    class Meta:
        exclude = ('definition',)
        model = models.Schema


class ProjectSchemaFilter(filters.FilterSet):
    class Meta:
        fields = '__all__'
        model = models.ProjectSchema


class EntityFilter(filters.FilterSet):
    class Meta:
        exclude = ('payload',)
        model = models.Entity
