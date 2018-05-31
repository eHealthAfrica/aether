from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from . import models


class PipelineSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        read_only=True,
        view_name='ui:pipeline-detail',
    )

    class Meta:
        model = models.Pipeline
        fields = '__all__'
