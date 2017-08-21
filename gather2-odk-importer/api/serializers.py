from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password as validate_pwd
from rest_framework import serializers

from .models import XForm
from .xform_utils import parse_xlsform, parse_xmlform


class XFormSerializer(serializers.ModelSerializer):

    url = serializers.HyperlinkedIdentityField('xform-detail', read_only=True)
    xls_file = serializers.FileField(
        write_only=True,
        allow_null=True,
        default=None,
        label='XLS Form',
        help_text='Upload file with XLS Form definition',
    )
    xml_file = serializers.FileField(
        write_only=True,
        allow_null=True,
        default=None,
        label='XML File',
        help_text='Upload file with XML Data definition',
    )

    def validate(self, value):
        if value['xls_file']:
            # extract data from file and put it on `xml_data`
            value['xml_data'] = parse_xlsform(value['xls_file'])
        value.pop('xls_file')

        if value['xml_file']:
            # extract data from file and put it on `xml_data`
            value['xml_data'] = parse_xmlform(value['xml_file'])
        value.pop('xml_file')

        return super(XFormSerializer, self).validate(value)

    class Meta:
        model = XForm
        fields = '__all__'


class SurveyorSerializer(serializers.ModelSerializer):
    password = serializers.CharField(style={'input_type': 'password'})
    # all the surveyors have as first name `surveyor`, display it as `role`
    role = serializers.CharField(
        label='Role',
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
