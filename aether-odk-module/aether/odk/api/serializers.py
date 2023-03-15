# Copyright (C) 2023 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password as validate_pwd
from django.utils.translation import gettext as _
from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from aether.sdk.drf.serializers import (
    DynamicFieldsModelSerializer,
    HyperlinkedIdentityField,
    HyperlinkedRelatedField,
    UsernameField,
)
from aether.sdk.multitenancy.serializers import (
    MtModelSerializer,
    MtPrimaryKeyRelatedField,
    MtUserRelatedField,
)
from aether.sdk.multitenancy.utils import add_user_to_realm

from .models import Project, XForm, MediaFile
from .xform_utils import parse_xform_file, validate_xform
from .surveyors_utils import get_surveyors, get_surveyor_group

from .collect.auth_utils import save_partial_digest


class MediaFileSerializer(DynamicFieldsMixin, DynamicFieldsModelSerializer):

    name = serializers.CharField(allow_null=True, default=None)
    media_file_url = HyperlinkedIdentityField(view_name='mediafile-content')

    xform = MtPrimaryKeyRelatedField(
        queryset=XForm.objects.all(),
        mt_field='project',
        style={'base_template': 'input.html'},
    )

    class Meta:
        model = MediaFile
        fields = '__all__'


class XFormSerializer(DynamicFieldsMixin, DynamicFieldsModelSerializer):

    url = HyperlinkedIdentityField(view_name='xform-detail')
    project_url = HyperlinkedRelatedField(
        view_name='project-detail',
        read_only=True,
        source='project',
    )

    surveyors = MtUserRelatedField(
        allow_null=True,
        default=[],
        help_text=_('If you do not specify any surveyors, EVERYONE will be able to access this xForm.'),
        label=_('Surveyors'),
        many=True,
        queryset=get_surveyors(),
    )

    xml_file = serializers.FileField(
        write_only=True,
        allow_null=True,
        default=None,
        label=_('XLS Form / XML File'),
        help_text=_('Upload an XLS Form or an XML File'),
    )

    # this will return all media files in one request call
    media_files = MediaFileSerializer(
        fields=('id', 'name'),
        many=True,
        read_only=True,
    )

    project = MtPrimaryKeyRelatedField(
        queryset=Project.objects.all(),
        style={'base_template': 'input.html'},
    )

    def validate(self, value):
        if value['xml_file']:
            try:
                # extract data from file and put it on `xml_data`
                value['xml_data'] = parse_xform_file(
                    filename=str(value['xml_file']),
                    content=value['xml_file'],
                )
                # validate xml data and link the possible errors to this field
                validate_xform(value['xml_data'])
            except Exception as e:
                raise serializers.ValidationError({'xml_file': str(e)})
        value.pop('xml_file')

        # check unique together
        if self.instance:  # in case of "update"
            for k, v in value.items():
                if k != 'surveyors':
                    setattr(self.instance, k, v)
            self.instance.full_clean()
        else:  # in case of "create"
            _instance = XForm(**{k: v for k, v in value.items() if k != 'surveyors'})
            _instance.full_clean()

        return super(XFormSerializer, self).validate(value)

    class Meta:
        model = XForm
        fields = '__all__'


class SurveyorSerializer(DynamicFieldsMixin, DynamicFieldsModelSerializer):

    username = UsernameField()
    password = serializers.CharField(
        allow_null=True,
        default=None,
        required=False,
        style={'input_type': 'password'},
        write_only=True,
    )

    projects = MtPrimaryKeyRelatedField(
        allow_null=True,
        default=None,
        many=True,
        queryset=Project.objects.all(),
        required=False,
    )
    project_names = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='name',
        source='projects',
    )

    def validate_password(self, value):
        if value is not None:
            validate_pwd(value)
        return value

    def create(self, validated_data):
        projects = validated_data.pop('projects', None)
        raw_password = validated_data.pop('password', None)
        if raw_password is None:
            # password is mandatory to create the surveyor but not to update it
            raise serializers.ValidationError({'password': [_('This field is required.')]})

        instance = self.Meta.model(**validated_data)
        self._save(instance, raw_password, projects)

        return instance

    def update(self, instance, validated_data):
        projects = validated_data.pop('projects', None)
        raw_password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        self._save(instance, raw_password, projects)

        return instance

    def _save(self, instance, raw_password, projects):
        request = self.context['request']

        if raw_password is not None and raw_password != instance.password:
            instance.set_password(raw_password)
        instance.save()

        if projects is not None:
            instance.projects.set(projects)
        instance.groups.add(get_surveyor_group())
        add_user_to_realm(request, instance)

        if raw_password is not None:
            # (required by digest authentication)
            save_partial_digest(request, instance, raw_password)

    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'password', 'projects', 'project_names',)


class ProjectSerializer(DynamicFieldsMixin, MtModelSerializer):

    url = HyperlinkedIdentityField(view_name='project-detail')

    surveyors = MtUserRelatedField(
        allow_null=True,
        default=[],
        help_text=_('If you do not specify any surveyors, EVERYONE will be able to access this project xForms.'),
        label=_('Surveyors'),
        many=True,
        queryset=get_surveyors(),
    )

    # this will return all linked xForms with media files in one request call
    xforms = XFormSerializer(
        omit=('url', 'project_url', 'project', 'avro_schema', 'kernel_id'),
        read_only=True,
        many=True,
    )

    class Meta:
        model = Project
        fields = '__all__'
