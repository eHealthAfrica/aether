from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password as validate_pwd
from rest_framework import serializers

from .models import XForm


class XFormSerializer(serializers.ModelSerializer):

    class Meta:
        model = XForm
        fields = '__all__'


class SurveyorSerializer(serializers.ModelSerializer):
    password = serializers.CharField(style={'input_type': 'password'})
    # all the surveyors have as first name `surveyor`, display it as `role`
    role = serializers.CharField(
        source='first_name',
        read_only=True,
        default='surveyor'
    )

    def validate_password(self, value):
        validate_pwd(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        instance.set_password(password)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr == 'password':
                if value != instance.password:
                    instance.set_password(value)
            else:
                setattr(instance, attr, value)
        instance.save()
        return instance

    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'password', 'role', )
