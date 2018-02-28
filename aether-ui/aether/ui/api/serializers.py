from rest_framework import serializers

from .models import Survey, Mask


class MaskSerializer(serializers.ModelSerializer):

    class Meta:
        model = Mask
        fields = '__all__'


class SurveySerializer(serializers.ModelSerializer):

    masks = MaskSerializer(many=True, read_only=True)

    class Meta:
        model = Survey
        fields = '__all__'
