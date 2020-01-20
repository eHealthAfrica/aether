# Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
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

from django.utils.translation import gettext as _
from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers
from django.conf import settings

from aether.sdk.drf.serializers import (
    DynamicFieldsModelSerializer,
    FilteredHyperlinkedRelatedField,
    HyperlinkedIdentityField,
    HyperlinkedRelatedField,
)
from aether.sdk.multitenancy.serializers import (
    MtPrimaryKeyRelatedField,
    MtModelSerializer,
)

from .utils import send_model_item_to_redis
from aether.python import utils
from aether.python.constants import MergeOptions as MERGE_OPTIONS

from . import models, validators


MERGE_CHOICES = (
    (MERGE_OPTIONS.overwrite.value, _('Overwrite (Do not merge)')),
    (MERGE_OPTIONS.lww.value, _('Last Write Wins (Target to Source)')),
    (MERGE_OPTIONS.fww.value, _('First Write Wins (Source to Target)'))
)
DEFAULT_MERGE = MERGE_OPTIONS.overwrite.value


class ProjectSerializer(DynamicFieldsMixin, MtModelSerializer):

    url = HyperlinkedIdentityField(view_name='project-detail')
    mappingset_url = FilteredHyperlinkedRelatedField(
        view_name='mappingset-list',
        lookup_field='project',
        read_only=True,
        source='mappingsets',
    )
    schemadecorators_url = FilteredHyperlinkedRelatedField(
        lookup_field='project',
        read_only=True,
        source='schemadecorators',
        view_name='schemadecorator-list',
    )

    class Meta:
        model = models.Project
        fields = '__all__'


class MappingSetSerializer(DynamicFieldsMixin, DynamicFieldsModelSerializer):

    url = HyperlinkedIdentityField(view_name='mappingset-detail')
    project_url = HyperlinkedRelatedField(
        view_name='project-detail',
        read_only=True,
        source='project',
    )
    mappings_url = FilteredHyperlinkedRelatedField(
        view_name='mapping-list',
        lookup_field='mappingset',
        read_only=True,
        source='mappings',
    )
    submissions_url = FilteredHyperlinkedRelatedField(
        view_name='submission-list',
        lookup_field='mappingset',
        read_only=True,
        source='submissions',
    )

    project = MtPrimaryKeyRelatedField(
        queryset=models.Project.objects.all(),
    )

    class Meta:
        model = models.MappingSet
        fields = '__all__'


class MappingSerializer(DynamicFieldsMixin, DynamicFieldsModelSerializer):

    url = HyperlinkedIdentityField(view_name='mapping-detail')
    mappingset_url = HyperlinkedRelatedField(
        view_name='mappingset-detail',
        read_only=True,
        source='mappingset',
    )
    schemadecorators_url = FilteredHyperlinkedRelatedField(
        lookup_field='mapping',
        read_only=True,
        source='schemadecorators',
        view_name='schemadecorator-list',
    )

    project = MtPrimaryKeyRelatedField(
        queryset=models.Project.objects.all(),
        required=False,
    )
    mappingset = MtPrimaryKeyRelatedField(
        queryset=models.MappingSet.objects.all(),
        mt_field='project',
    )

    class Meta:
        model = models.Mapping
        fields = '__all__'


class AttachmentSerializer(DynamicFieldsMixin, DynamicFieldsModelSerializer):

    name = serializers.CharField(allow_null=True, default=None)
    submission_revision = serializers.CharField(allow_null=True, default=None)

    url = HyperlinkedIdentityField(view_name='attachment-detail')
    attachment_file_url = HyperlinkedIdentityField(view_name='attachment-content')
    submission_url = HyperlinkedRelatedField(
        view_name='submission-detail',
        source='submission',
        read_only=True,
    )

    submission = MtPrimaryKeyRelatedField(
        queryset=models.Submission.objects.all(),
        mt_field='project',
    )

    class Meta:
        model = models.Attachment
        fields = '__all__'


class SubmissionListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        submissions = [models.Submission(**s) for s in validated_data]
        for submission in submissions:
            submission.project = submission.mappingset.project

        # bulk database operation
        results = models.Submission.objects.bulk_create(submissions)
        # send to redis
        submission_list = list(submissions)
        for s in submission_list:
            send_model_item_to_redis(s)
        return results


class SubmissionSerializer(DynamicFieldsMixin, DynamicFieldsModelSerializer):

    url = HyperlinkedIdentityField(view_name='submission-detail')
    project_url = HyperlinkedRelatedField(
        view_name='project-detail',
        source='project',
        read_only=True,
    )
    mappingset_url = HyperlinkedRelatedField(
        view_name='mappingset-detail',
        source='mappingset',
        read_only=True,
    )
    entities_url = FilteredHyperlinkedRelatedField(
        view_name='entity-list',
        lookup_field='submission',
        read_only=True,
        source='entities',
    )
    attachments_url = FilteredHyperlinkedRelatedField(
        view_name='attachment-list',
        lookup_field='submission',
        read_only=True,
        source='attachments',
    )

    # this will return all linked attachment files
    attachments = AttachmentSerializer(
        fields=('id', 'name'),
        many=True,
        read_only=True,
    )

    project = MtPrimaryKeyRelatedField(
        queryset=models.Project.objects.all(),
        required=False,
    )

    mappingset = MtPrimaryKeyRelatedField(
        queryset=models.MappingSet.objects.all(),
        mt_field='project',
        required=False,
    )

    def create(self, validated_data):
        if not validated_data.get('mappingset'):
            raise serializers.ValidationError(
                {'mappingset': [_('Mapping set must be provided on initial submission')]}
            )

        return super(SubmissionSerializer, self).create(validated_data)

    class Meta:
        model = models.Submission
        fields = '__all__'
        list_serializer_class = SubmissionListSerializer


class SchemaSerializer(DynamicFieldsMixin, DynamicFieldsModelSerializer):

    url = HyperlinkedIdentityField(view_name='schema-detail')
    schemadecorators_url = FilteredHyperlinkedRelatedField(
        view_name='schemadecorator-list',
        lookup_field='schema',
        read_only=True,
        source='schemadecorators',
    )

    class Meta:
        model = models.Schema
        fields = '__all__'


class SchemaDecoratorSerializer(DynamicFieldsMixin, DynamicFieldsModelSerializer):

    url = HyperlinkedIdentityField(view_name='schemadecorator-detail')
    project_url = HyperlinkedRelatedField(
        view_name='project-detail',
        read_only=True,
        source='project',
    )
    schema_url = HyperlinkedRelatedField(
        view_name='schema-detail',
        read_only=True,
        source='schema',
    )
    entities_url = FilteredHyperlinkedRelatedField(
        view_name='entity-list',
        lookup_field='schemadecorator',
        read_only=True,
        source='entities',
    )
    mappings_url = FilteredHyperlinkedRelatedField(
        view_name='mapping-list',
        lookup_field='schemadecorator',
        read_only=True,
        source='mappings',
    )

    schema_definition = serializers.JSONField(
        read_only=True,
        source='schema.definition',
    )

    project = MtPrimaryKeyRelatedField(
        queryset=models.Project.objects.all(),
    )

    class Meta:
        model = models.SchemaDecorator
        fields = '__all__'


class EntityListSerializer(serializers.ListSerializer):

    def create(self, validated_data):
        errors = []
        entities = []
        # remove helper field and validate entity
        for i in validated_data:
            i.pop('merge')
            try:
                # set ignore_submission_check to True to avoid a race condition on bulk submissions
                i['project'] = validators.validate_entity_project(i)
                entity = models.Entity(**i)
                entity.clean()
                entities.append(entity)
            except Exception as e:
                errors.append(str(e))

        if errors:
            # reject ALL if ANY invalid entities are included
            raise(serializers.ValidationError(errors))
        # bulk database operation
        try:
            created_entities = models.Entity.objects.bulk_create(entities)
            if settings.WRITE_ENTITIES_TO_REDIS:  # pragma: no cover : .env setting
                # send created entities to redis
                for entity in entities:
                    send_model_item_to_redis(entity)
            return created_entities
        except Exception as e:  # pragma: no cover : happens only when redis is offline
            raise(serializers.ValidationError(e))


class EntitySerializer(DynamicFieldsMixin, DynamicFieldsModelSerializer):

    url = HyperlinkedIdentityField(view_name='entity-detail')
    project_url = HyperlinkedRelatedField(
        view_name='project-detail',
        read_only=True,
        source='project',
    )
    schema_url = HyperlinkedRelatedField(
        view_name='schema-detail',
        read_only=True,
        source='schema',
    )
    schemadecorator_url = HyperlinkedRelatedField(
        view_name='schemadecorator-detail',
        read_only=True,
        source='schemadecorator',
    )
    submission_url = HyperlinkedRelatedField(
        view_name='submission-detail',
        read_only=True,
        source='submission',
    )
    mapping_url = HyperlinkedRelatedField(
        view_name='mapping-detail',
        read_only=True,
        source='mapping',
    )

    # this field is used to update existing entities, indicates the MERGE strategy
    merge = serializers.ChoiceField(write_only=True, choices=MERGE_CHOICES, default=DEFAULT_MERGE)

    # this field is used to include the linked nested entities
    resolved = serializers.JSONField(read_only=True, default={})

    # this will return all linked attachment files in one request call
    attachments = AttachmentSerializer(
        fields=('id', 'name'),
        many=True,
        read_only=True,
        source='submission.attachments',
    )

    project = MtPrimaryKeyRelatedField(
        queryset=models.Project.objects.all(),
        required=False,
    )
    submission = MtPrimaryKeyRelatedField(
        queryset=models.Submission.objects.all(),
        mt_field='mappingset__project',
        required=False,
    )
    mapping = MtPrimaryKeyRelatedField(
        queryset=models.Mapping.objects.all(),
        mt_field='mappingset__project',
        required=False,
    )
    schemadecorator = MtPrimaryKeyRelatedField(
        queryset=models.SchemaDecorator.objects.all(),
        mt_field='project',
        required=False,
    )

    def create(self, validated_data):
        # remove helper field
        validated_data.pop('merge')

        try:
            validated_data['project'] = validators.validate_entity_project(validated_data)
            return super(EntitySerializer, self).create(validated_data)
        except Exception as e:
            raise serializers.ValidationError(e)

    def update(self, instance, validated_data):
        # find out payload
        if validated_data.get('payload'):
            validated_data['payload'] = utils.merge_objects(
                source=instance.payload,
                target=validated_data.get('payload'),
                direction=validated_data.pop('merge', DEFAULT_MERGE),
            )
        try:
            return super(EntitySerializer, self).update(instance, validated_data)
        except Exception as e:
            raise serializers.ValidationError(e)

    class Meta:
        model = models.Entity
        fields = '__all__'
        list_serializer_class = EntityListSerializer


class ProjectStatsSerializer(DynamicFieldsMixin, DynamicFieldsModelSerializer):

    first_submission = serializers.DateTimeField()
    last_submission = serializers.DateTimeField()
    submissions_count = serializers.IntegerField()
    attachments_count = serializers.IntegerField()
    entities_count = serializers.IntegerField()

    class Meta:
        model = models.Project
        fields = (
            'id', 'name', 'created', 'active',
            'first_submission', 'last_submission',
            'submissions_count', 'attachments_count', 'entities_count',
        )


class MappingSetStatsSerializer(DynamicFieldsMixin, DynamicFieldsModelSerializer):

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
    mapping_definition = serializers.JSONField(validators=[validators.wrapper_validate_mapping_definition])
    schemas = serializers.JSONField(validators=[validators.wrapper_validate_schemas])
