from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from . import models


class EntityTypeSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        read_only=True,
        view_name='ui:entitytype-detail',
    )

    class Meta:
        model = models.EntityType
        fields = '__all__'


class PipelineSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        read_only=True,
        view_name='ui:pipeline-detail',
    )
    entity_types = EntityTypeSerializer(many=True, read_only=True)

    class Meta:
        model = models.Pipeline
        fields = '__all__'
