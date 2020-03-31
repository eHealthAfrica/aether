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

import uuid
from django.utils.translation import gettext as _
from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers
from django.conf import settings

from aether.sdk.drf.serializers import (
    DynamicFieldsSerializer,
    DynamicFieldsModelSerializer,
    FilteredHyperlinkedRelatedField,
    HyperlinkedIdentityField,
    HyperlinkedRelatedField,
    UserNameField,
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


class KernelBaseSerializer(DynamicFieldsSerializer):
    '''
    Base field for Serializers that don't inherit from
    ModelSerializer via DynamicFieldsModelSerializer
    '''
    id = serializers.UUIDField(required=False, default=uuid.uuid4)
    revision = serializers.CharField(required=False, default='1')
    modified = serializers.CharField(read_only=True)


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

    schema_name = serializers.CharField(
        read_only=True,
        source='schema.name',
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
        entities = []
        # remove helper field and validate entity
        for entity_data in validated_data:
            entity_data.pop('merge', None)
            try:
                # set ignore_submission_check to True to avoid a race condition on bulk submissions
                entity_data['project'] = validators.validate_entity_project(entity_data)
                entity = models.Entity(**entity_data)
                entity.clean()
                entities.append(entity)
            except Exception as e:
                raise(serializers.ValidationError(str(e)))

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


class EntitySerializer(DynamicFieldsMixin, KernelBaseSerializer):
    payload = serializers.JSONField()
    status = serializers.ChoiceField(choices=models.ENTITY_STATUS_CHOICES)
    mapping_revision = serializers.CharField(read_only=True)

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
            return models.Entity.objects.create(**validated_data)
        except Exception as e:
            raise serializers.ValidationError(e)

    def update(self, instance, validated_data):
        # apply update policy if there's a payload
        if validated_data.get('payload'):
            instance.payload = utils.merge_objects(
                source=instance.payload,
                target=validated_data.get('payload'),
                direction=validated_data.pop('merge', DEFAULT_MERGE),
            )
        # the metadata should always be applied from the new version
        # keep this local, only referenced here
        _user_updatable_metadata = ['status', 'revision']
        for k in _user_updatable_metadata:
            if validated_data.get(k):
                setattr(instance, k, validated_data.get(k))
        try:
            instance.save()
            return instance
        except Exception as e:
            raise serializers.ValidationError(e)

    class Meta:
        list_serializer_class = EntityListSerializer


class SubmissionListSerializer(serializers.ListSerializer):

    def create(self, validated_data):
        submissions = self._get_validated_list(validated_data)

        # bulk database operation
        results = models.Submission.objects.bulk_create(submissions)
        return self._send_to_redis(results)

    def update(self, instance, validated_data):
        # cannot use validated data, take the initial data
        for data in self.initial_data:
            entities_data = [
                {**e, 'submission': data['id']}  # add submission id
                for e in data.pop('extracted_entities', [])
            ]

            if entities_data:
                # this is a bulk update from extractor that includes the entities
                entities = EntitySerializer(
                    data=entities_data,
                    many=True,
                    context=self.context,
                )
                entities.is_valid(raise_exception=True)
                entities.save()

        fields = set()
        for data in validated_data:
            data.pop('extracted_entities', None)
            for k in data.keys():
                fields.add(k)
        fields.remove('id')

        # bulk database operation
        submissions = self._get_validated_list(validated_data)
        models.Submission.objects.bulk_update(submissions, fields)
        return submissions

    def _get_validated_list(self, validated_data):
        submissions = [models.Submission(**s) for s in validated_data]
        for submission in submissions:
            submission.project = submission.mappingset.project
        return submissions

    def _send_to_redis(self, submissions):
        submission_list = list(submissions)
        for s in submission_list:
            send_model_item_to_redis(s)
        return submissions


class SubmissionSerializer(DynamicFieldsMixin, KernelBaseSerializer):

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

    payload = serializers.JSONField()

    project = MtPrimaryKeyRelatedField(
        queryset=models.Project.objects.all(),
        required=False,
    )

    is_extracted = serializers.BooleanField(default=False)

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
        try:
            return models.Submission.objects.create(**validated_data)
        except Exception as e:                    # pragma: no cover : don't know how to trigger
            raise serializers.ValidationError(e)  # without first triggering VE on the serializer

    def update(self, instance, validated_data):
        for k, v in validated_data.items():
            setattr(instance, k, v)

        try:
            instance.save()
            return instance
        except Exception as e:  # pragma: no cover
            raise serializers.ValidationError(e)

    class Meta:
        list_serializer_class = SubmissionListSerializer


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


class ExportTaskFileUrlField(HyperlinkedIdentityField):

    def __init__(self, view_name=None, **kwargs):
        super(ExportTaskFileUrlField, self).__init__('exporttask-file_content', **kwargs)

    def get_url(self, obj, view_name, request, format):
        return self.reverse(
            viewname=view_name,
            kwargs={'pk': str(obj.task.pk), 'file_pk': str(obj.pk)},
            request=request,
            format=None,
        )


class ExportTaskFileSerializer(DynamicFieldsModelSerializer):

    file_url = ExportTaskFileUrlField(read_only=True, lookup_field='task__pk')

    class Meta:
        model = models.ExportTaskFile
        fields = ('name', 'file_url', 'size', 'md5sum',)


class ExportTaskSerializer(DynamicFieldsMixin, DynamicFieldsModelSerializer):

    created_by = UserNameField()

    project = MtPrimaryKeyRelatedField(
        read_only=True,
    )
    project_name = serializers.SlugRelatedField(
        read_only=True,
        slug_field='name',
        source='project',
    )

    # this will return all files in one request call
    files = ExportTaskFileSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = models.ExportTask
        fields = '__all__'
