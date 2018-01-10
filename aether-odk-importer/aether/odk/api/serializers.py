from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password as validate_pwd
from django.utils.translation import ugettext as _
from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from .models import Mapping, XForm, MediaFile
from .xform_utils import parse_file
from .surveyors_utils import get_surveyors, flag_as_surveyor


class MediaFileSerializer(DynamicFieldsMixin, serializers.ModelSerializer):

    name = serializers.CharField(allow_null=True, default=None)

    class Meta:
        model = MediaFile
        fields = '__all__'


class XFormSerializer(DynamicFieldsMixin, serializers.ModelSerializer):

    url = serializers.HyperlinkedIdentityField('xform-detail', read_only=True)
    mapping_url = serializers.HyperlinkedRelatedField(
        'mapping-detail',
        source='mapping',
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

    media_files = serializers.PrimaryKeyRelatedField(
        label=_('Media files'),
        many=True,
        queryset=MediaFile.objects.all(),
        allow_null=True,
        default=[],
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

    def update(self, instance, validated_data):
        # extract updated media files list
        media_files = validated_data.pop('media_files')
        # delete media files not present in the updated list
        MediaFile.objects.filter(xform=instance.pk) \
                         .exclude(pk__in=[mf.pk for mf in media_files]) \
                         .delete()
        # update xform as usual
        return super(XFormSerializer, self).update(instance, validated_data)

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

    media_files = MediaFileSerializer(many=True, read_only=True)

    class Meta:
        model = XForm
        fields = '__all__'


class MappingSerializer(DynamicFieldsMixin, serializers.ModelSerializer):

    url = serializers.HyperlinkedIdentityField('mapping-detail', read_only=True)
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
        model = Mapping
        fields = '__all__'
