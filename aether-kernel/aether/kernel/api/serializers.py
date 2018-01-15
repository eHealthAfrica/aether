# -*- coding: utf-8 -*-
from rest_framework import serializers
from rest_framework.reverse import reverse
from drf_dynamic_fields import DynamicFieldsMixin

from . import models
from . import utils


import urllib


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
    mappings_url = FilteredHyperlinkedRelatedField(
        lookup_field='project',
        read_only=True,
        source='mappings',
        view_name='mapping-list',
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


class MappingSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        read_only=True,
        view_name='mapping-detail',
    )
    project_url = serializers.HyperlinkedRelatedField(
        read_only=True,
        source='project',
        view_name='project-detail',
    )
    submissions_url = FilteredHyperlinkedRelatedField(
        lookup_field='mapping',
        read_only=True,
        source='submissions',
        view_name='submission-list',
    )

    class Meta:
        model = models.Mapping
        fields = '__all__'


class SubmissionSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='submission-detail',
        read_only=True
    )
    mapping_url = serializers.HyperlinkedRelatedField(
        view_name='mapping-detail',
        source='mapping',
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

    def create(self, validated_data):
        try:
            if 'mapping' in validated_data:
                if 'revision' and 'map_revision' in validated_data:
                    submission = models.Submission(
                        revision=validated_data.pop('revision'),
                        map_revision=validated_data.pop('map_revision'),
                        payload=validated_data.pop('payload'),
                        mapping=validated_data.pop('mapping')
                    )
                else:
                    submission = models.Submission(
                        payload=validated_data.pop('payload'),
                        mapping=validated_data.pop('mapping')
                    )

                utils.extract_create_entities(submission)

            elif 'parent_lookup_mapping' in self.context.get('request').parser_context['kwargs']:
                kwargs = self.context.get('request').parser_context['kwargs']
                mapping_id = kwargs['parent_lookup_mapping']
                mapping = models.Mapping.objects.get(pk=mapping_id)
                if 'revision' and 'map_revision' in validated_data:
                    submission = models.Submission(
                        revision=validated_data.pop('revision'),
                        map_revision=validated_data.pop('map_revision'),
                        payload=validated_data.pop('payload'),
                        mapping=mapping_id
                    )
                else:
                    submission = models.Submission(
                        payload=validated_data.pop('payload'),
                        mapping=mapping
                    )

                utils.extract_create_entities(submission)
            else:
                if 'revision' and 'map_revision' in validated_data:
                    submission = models.Submission(
                        revision=validated_data.pop('revision'),
                        map_revision=validated_data.pop('map_revision'),
                        payload=validated_data.pop('payload'),
                    )
                else:
                    submission = models.Submission(
                        payload=validated_data.pop('payload')
                    )
                # Save the submission to the db
                submission.save()

            return submission
        except Exception as e:
            raise serializers.ValidationError({
                'description': 'Submission validation failed'
            })

    class Meta:
        model = models.Submission
        fields = '__all__'


class AttachmentSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    name = serializers.CharField(allow_null=True, default=None)
    submission_revision = serializers.CharField(allow_null=True, default=None)

    url = serializers.HyperlinkedIdentityField('attachment-detail', read_only=True)
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

    def create(self, validated_data):
        entity = models.Entity(
            payload=validated_data.pop('payload'),
            status=validated_data.pop('status'),
            projectschema=validated_data.pop('projectschema'),
        )
        if 'submission' in validated_data:
            entity.submission = validated_data.pop('submission')
        if 'id' in validated_data:
            entity.id = validated_data.pop('id')
        entity.payload['_id'] = str(entity.id)
        entity.save()
        return entity

    class Meta:
        model = models.Entity
        fields = '__all__'
