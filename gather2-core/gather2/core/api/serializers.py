# -*- coding: utf-8 -*-
from rest_framework import serializers

from . import models
from . import utils


class ProjectSerializer(serializers.ModelSerializer):

    url = serializers.HyperlinkedIdentityField('project-detail',
                                               read_only=True, lookup_field='name')

    mappings_url = serializers.HyperlinkedIdentityField(
        'project_mapping-list',
        read_only=True,
        lookup_url_kwarg='parent_lookup_project'
    )
    projectschemas_url = serializers.HyperlinkedIdentityField(
        'project_projectschema-list',
        read_only=True,
        lookup_url_kwarg='parent_lookup_project',
        lookup_field='name'
    )

    class Meta:
        model = models.Project
        fields = '__all__'


class MappingSerializer(serializers.ModelSerializer):

    url = serializers.HyperlinkedIdentityField('mapping-detail',
                                               read_only=True, lookup_field='name')

    project_url = serializers.HyperlinkedRelatedField(
        view_name='project-detail',
        source='project',
        read_only=True,
        lookup_field='name'
    )
    responses_url = serializers.HyperlinkedIdentityField(
        'mapping_response-list',
        read_only=True,
        lookup_url_kwarg='parent_lookup_mapping'
    )

    class Meta:
        model = models.Mapping
        fields = '__all__'


class ResponseSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        if 'mapping' in validated_data:
            if 'revision' and 'map_revision' in validated_data:
                response = models.Response(
                    revision=validated_data.pop('revision'),
                    map_revision=validated_data.pop('map_revision'),
                    payload=validated_data.pop('payload'),
                    mapping=validated_data.pop('mapping')
                )
            else:
                response = models.Response(
                    payload=validated_data.pop('payload'),
                    mapping=validated_data.pop('mapping')
                )

            utils.extract_create_entities(response)

        elif 'parent_lookup_mapping' in self.context.get('request').parser_context['kwargs']:
            kwargs = self.context.get('request').parser_context['kwargs']
            mapping_id = kwargs['parent_lookup_mapping']
            mapping = models.Mapping.objects.get(pk=mapping_id)
            if 'revision' and 'map_revision' in validated_data:
                response = models.Response(
                    revision=validated_data.pop('revision'),
                    map_revision=validated_data.pop('map_revision'),
                    payload=validated_data.pop('payload'),
                    mapping=mapping_id
                )
            else:
                response = models.Response(
                    payload=validated_data.pop('payload'),
                    mapping=mapping
                )

            utils.extract_create_entities(response)
        else:
            if 'revision' and 'map_revision' in validated_data:
                response = models.Response(
                    revision=validated_data.pop('revision'),
                    map_revision=validated_data.pop('revision'),
                    payload=validated_data.pop('payload'),
                )
            else:
                response = models.Response(
                    payload=validated_data.pop('payload')
                )
            # Save the response to the db
            response.save()

        return response

    url = serializers.HyperlinkedIdentityField('response-detail', read_only=True)

    mapping_url = serializers.HyperlinkedRelatedField(
        'mapping-detail',
        source='mapping',
        read_only=True,
        lookup_field='name'
    )
    entities_url = serializers.HyperlinkedIdentityField(
        'response_entity-list',
        read_only=True,
        lookup_url_kwarg='parent_lookup_response'
    )

    class Meta:
        model = models.Response
        fields = '__all__'


class SchemaSerializer(serializers.ModelSerializer):

    url = serializers.HyperlinkedIdentityField('schema-detail',
                                               read_only=True, lookup_field='name')
    projectschemas_url = serializers.HyperlinkedIdentityField(
        'schema_projectschema-list',
        read_only=True,
        lookup_url_kwarg='parent_lookup_schema',
        lookup_field='name'
    )

    class Meta:
        model = models.Schema
        fields = '__all__'


class ProjectSchemaSerializer(serializers.ModelSerializer):

    url = serializers.HyperlinkedIdentityField('projectschema-detail',
                                               read_only=True, lookup_field='name')
    project_url = serializers.HyperlinkedRelatedField(
        'project-detail',
        source='project',
        read_only=True,
        lookup_field='name'
    )
    schema_url = serializers.HyperlinkedRelatedField(
        'schema-detail',
        source='schema',
        read_only=True,
        lookup_field='name'
    )
    entities_url = serializers.HyperlinkedIdentityField(
        'projectschema_entity-list',
        read_only=True,
        lookup_url_kwarg='parent_lookup_projectschema',
        lookup_field='name'
    )

    class Meta:
        model = models.ProjectSchema
        fields = '__all__'


class EntitySerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        entity = models.Entity(
            payload=validated_data.pop('payload'),
            status=validated_data.pop('status'),
            projectschema=validated_data.pop('projectschema'),
        )
        if "response" in validated_data:
            entity.response = validated_data.pop('response')
        if 'id' in validated_data:
            entity.id = validated_data.pop('id')
        entity.payload['_id'] = str(entity.id)
        entity.save()
        return entity

    url = serializers.HyperlinkedIdentityField('entity-detail', read_only=True)
    projectschema_url = serializers.HyperlinkedRelatedField(
        'projectschema-detail',
        source='projectschema',
        read_only=True,
        lookup_field='name'
    )

    class Meta:
        model = models.Entity
        fields = '__all__'
