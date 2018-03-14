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
    instanceID = filters.CharFilter(
        name='payload__meta__instanceID',
        lookup_expr='exact',
    )

    class Meta:
        exclude = ('payload',)
        model = models.Submission


class AttachmentFilter(filters.FilterSet):
    class Meta:
        exclude = ('attachment_file',)
        model = models.Attachment


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
