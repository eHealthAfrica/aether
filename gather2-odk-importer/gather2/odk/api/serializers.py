from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password as validate_pwd
from django.utils.translation import ugettext as _
from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from .models import Survey, XForm
from .xform_utils import parse_file
from .surveyors_utils import get_surveyors, flag_as_surveyor


class XFormSerializer(DynamicFieldsMixin, serializers.ModelSerializer):

    url = serializers.HyperlinkedIdentityField('xform-detail', read_only=True)
    survey_url = serializers.HyperlinkedRelatedField(
        'survey-detail',
        source='survey',
        read_only=True
    )

    surveyors = serializers.PrimaryKeyRelatedField(
        label=_('Surveyors'),
        many=True,
        queryset=get_surveyors(),
        allow_null=True,
        default=[],
    )

    xml_file = serializers.FileField(
        write_only=True,
        allow_null=True,
        default=None,
        label=_('XLS Form / XML File'),
        help_text=_('Upload an XLS Form or an XML File'),
    )

    def validate(self, value):
        if value['xml_file']:
            try:
                # extract data from file and put it on `xml_data`
                value['xml_data'] = parse_file(
                    filename=str(value['xml_file']),
                    content=value['xml_file'],
                )
            except Exception as e:
                raise serializers.ValidationError({'xml_file': str(e)})
        value.pop('xml_file')

        return super(XFormSerializer, self).validate(value)

    class Meta:
        model = XForm
        fields = '__all__'


class SurveyorSerializer(DynamicFieldsMixin, serializers.ModelSerializer):

    password = serializers.CharField(style={'input_type': 'password'})

    def validate_password(self, value):
        validate_pwd(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        instance.set_password(password)
        instance.save()
        flag_as_surveyor(instance)

        return instance

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr == 'password':
                if value != instance.password:
                    instance.set_password(value)
            else:
                setattr(instance, attr, value)
        instance.save()
        flag_as_surveyor(instance)

        return instance

    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'password', )


class XFormSimpleSerializer(DynamicFieldsMixin, serializers.ModelSerializer):

    class Meta:
        model = XForm
        fields = '__all__'


class SurveySerializer(DynamicFieldsMixin, serializers.ModelSerializer):

    url = serializers.HyperlinkedIdentityField('survey-detail', read_only=True)
    surveyors = serializers.PrimaryKeyRelatedField(
        label=_('Surveyors'),
        many=True,
        queryset=get_surveyors(),
        allow_null=True,
        default=[],
    )
    # this will return all linked xForms in one request call
    xforms = XFormSimpleSerializer(read_only=True, many=True)

    class Meta:
        model = Survey
        fields = '__all__'
