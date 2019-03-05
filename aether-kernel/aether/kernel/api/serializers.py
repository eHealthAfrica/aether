# -*- coding: utf-8 -*-

# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
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

import urllib

from django.utils.translation import ugettext as _
from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers
from rest_framework.reverse import reverse

from .constants import MergeOptions as MERGE_OPTIONS
from .entity_extractor import run_entity_extraction, ENTITY_EXTRACTION_ERRORS

from . import models, utils, validators


MERGE_CHOICES = (
    (MERGE_OPTIONS.overwrite.value, _('Overwrite (Do not merge)')),
    (MERGE_OPTIONS.lww.value, _('Last Write Wins (Target to Source)')),
    (MERGE_OPTIONS.fww.value, _('First Write Wins (Source to Target)'))
)
DEFAULT_MERGE = MERGE_OPTIONS.overwrite.value


class FilteredHyperlinkedRelatedField(serializers.HyperlinkedRelatedField):
    '''
    This custom field does essentially the same thing as
    serializers.HyperlinkedRelatedField. The only difference is that the url of
    a foreign key relationship will be:

        {
            ...
            'entities_url': '/entities?projectschema=<projectschema-id>'
            ...
        }

    Instead of:

        {
            ...
            'entities': [
                '/entities/<entity-id>',
                '/entities/<entity-id>',
            ]
            ...
        }

    '''

    def get_url(self, obj, view_name, request, format):
        lookup_field_value = obj.instance.pk
        result = '{}?{}'.format(
            reverse(view_name, kwargs={}, request=request, format=format),
            urllib.parse.urlencode({self.lookup_field: lookup_field_value})
        )
        return result


class ProjectSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        read_only=True,
        view_name='project-detail',
    )
    mappingset_url = FilteredHyperlinkedRelatedField(
        lookup_field='project',
        read_only=True,
        source='mappingsets',
        view_name='mappingset-list',
    )
    projectschemas_url = FilteredHyperlinkedRelatedField(
        lookup_field='project',
        read_only=True,
        source='projectschemas',
        view_name='projectschema-list',
    )

    class Meta:
        model = models.Project
        fields = '__all__'


class MappingSetSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        read_only=True,
        view_name='mappingset-detail',
    )
    project_url = serializers.HyperlinkedRelatedField(
        read_only=True,
        source='project',
        view_name='project-detail',
    )
    mappings_url = FilteredHyperlinkedRelatedField(
        lookup_field='mappingset',
        read_only=True,
        source='mappings',
        view_name='mapping-list',
    )
    submissions_url = FilteredHyperlinkedRelatedField(
        lookup_field='mappingset',
        read_only=True,
        source='submissions',
        view_name='submission-list',
    )

    class Meta:
        model = models.MappingSet
        fields = '__all__'


class MappingSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        read_only=True,
        view_name='mapping-detail',
    )
    mappingset_url = serializers.HyperlinkedRelatedField(
        read_only=True,
        source='mappingset',
        view_name='mappingset-detail',
    )

    projectschemas_url = FilteredHyperlinkedRelatedField(
        lookup_field='mapping',
        read_only=True,
        source='projectschemas',
        view_name='projectschema-list',
    )

    class Meta:
        model = models.Mapping
        fields = '__all__'


class AttachmentSerializerNested(DynamicFieldsMixin, serializers.ModelSerializer):
    name = serializers.CharField(read_only=True)
    url = serializers.CharField(read_only=True, source='attachment_file_url')

    class Meta:
        model = models.Attachment
        fields = ('name', 'url')


class SubmissionSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='submission-detail',
        read_only=True
    )
    project_url = serializers.HyperlinkedRelatedField(
        view_name='project-detail',
        source='project',
        read_only=True,
    )
    mappingset_url = serializers.HyperlinkedRelatedField(
        view_name='mappingset-detail',
        source='mappingset',
        read_only=True,
    )
    entities_url = FilteredHyperlinkedRelatedField(
        lookup_field='submission',
        view_name='entity-list',
        read_only=True,
        source='entities',
    )
    attachments_url = FilteredHyperlinkedRelatedField(
        lookup_field='submission',
        view_name='attachment-list',
        read_only=True,
        source='attachments',
    )

    # this will return all linked attachment files
    # (name, relative url) in one request call
    attachments = AttachmentSerializerNested(many=True, read_only=True)

    def create(self, validated_data):
        instance = super(SubmissionSerializer, self).create(validated_data)
        try:
            run_entity_extraction(instance)
        except Exception as e:
            instance.payload[ENTITY_EXTRACTION_ERRORS] = instance.payload.get(ENTITY_EXTRACTION_ERRORS, [])
            instance.payload[ENTITY_EXTRACTION_ERRORS] += [str(e)]
            instance.save()
        return instance

    class Meta:
        model = models.Submission
        fields = '__all__'


class AttachmentSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    name = serializers.CharField(allow_null=True, default=None)
    submission_revision = serializers.CharField(allow_null=True, default=None)

    url = serializers.HyperlinkedIdentityField('attachment-detail', read_only=True)
    attachment_file_url = serializers.CharField(read_only=True)
    submission_url = serializers.HyperlinkedRelatedField(
        'submission-detail',
        source='submission',
        read_only=True
    )

    class Meta:
        model = models.Attachment
        fields = '__all__'


class SchemaSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='schema-detail',
        read_only=True,
    )
    projectschemas_url = FilteredHyperlinkedRelatedField(
        lookup_field='schema',
        read_only=True,
        source='projectschemas',
        view_name='projectschema-list',
    )

    class Meta:
        model = models.Schema
        fields = '__all__'


class ProjectSchemaSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        read_only=True,
        view_name='projectschema-detail',
    )
    project_url = serializers.HyperlinkedRelatedField(
        view_name='project-detail',
        source='project',
        read_only=True,
    )
    schema_url = serializers.HyperlinkedRelatedField(
        view_name='schema-detail',
        source='schema',
        read_only=True,
    )
    entities_url = FilteredHyperlinkedRelatedField(
        lookup_field='projectschema',
        read_only=True,
        source='entities',
        view_name='entity-list',
    )
    mappings_url = FilteredHyperlinkedRelatedField(
        lookup_field='projectschema',
        read_only=True,
        source='mappings',
        view_name='mapping-list',
    )

    schema_definition = serializers.JSONField(
        read_only=True,
        source='schema.definition',
    )

    class Meta:
        model = models.ProjectSchema
        fields = '__all__'


class EntitySerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='entity-detail',
        read_only=True
    )
    projectschema_url = serializers.HyperlinkedRelatedField(
        read_only=True,
        source='projectschema',
        view_name='projectschema-detail',
    )
    submission_url = serializers.HyperlinkedRelatedField(
        read_only=True,
        source='submission',
        view_name='submission-detail',
    )

    # this field is used to update existing entities, indicates the MERGE strategy
    merge = serializers.ChoiceField(write_only=True, choices=MERGE_CHOICES, default=DEFAULT_MERGE)

    # this field is used to include the linked nested entities
    resolved = serializers.JSONField(read_only=True, default={})

    # this will return all linked attachment files
    # (name, relative url) in one request call
    attachments = AttachmentSerializerNested(
        many=True,
        read_only=True,
        source='submission.attachments',
    )

    def create(self, validated_data):
        # remove helper field
        validated_data.pop('merge')
        try:
            return super(EntitySerializer, self).create(validated_data)
        except Exception as e:
            raise serializers.ValidationError(e)

    def update(self, instance, validated_data):
        # find out payload
        validated_data['payload'] = utils.merge_objects(
            source=instance.payload,
            target=validated_data.get('payload', {}),
            direction=validated_data.pop('merge', DEFAULT_MERGE),
        )

        try:
            return super(EntitySerializer, self).update(instance, validated_data)
        except Exception as e:
            raise serializers.ValidationError(e)

    class Meta:
        model = models.Entity
        fields = '__all__'


class ProjectStatsSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    first_submission = serializers.DateTimeField()
    last_submission = serializers.DateTimeField()
    submissions_count = serializers.IntegerField()
    attachments_count = serializers.IntegerField()
    entities_count = serializers.IntegerField()

    class Meta:
        model = models.Project
        fields = (
            'id', 'name', 'created',
            'first_submission', 'last_submission',
            'submissions_count', 'attachments_count', 'entities_count',
        )


class MappingSetStatsSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    first_submission = serializers.DateTimeField()
    last_submission = serializers.DateTimeField()
    submissions_count = serializers.IntegerField()
    attachments_count = serializers.IntegerField()
    entities_count = serializers.IntegerField()

    class Meta:
        model = models.MappingSet
        fields = (
            'id', 'name', 'created',
            'first_submission', 'last_submission',
            'submissions_count', 'attachments_count', 'entities_count',
        )


class MappingValidationSerializer(serializers.Serializer):
    submission_payload = serializers.JSONField()
    mapping_definition = serializers.JSONField(validators=[validators.validate_mapping_definition])
    schemas = serializers.JSONField(validators=[validators.validate_schemas])
