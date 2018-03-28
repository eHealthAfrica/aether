from rest_framework import serializers

from . import models


class PipelineSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        read_only=True,
        view_name='ui:pipeline-detail',
    )

    class Meta:
        model = models.Pipeline
        fields = '__all__'
