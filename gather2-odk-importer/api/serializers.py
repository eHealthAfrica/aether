from .models import XForm
from rest_framework import serializers


class XFormSerializer(serializers.ModelSerializer):

    class Meta:
        model = XForm
