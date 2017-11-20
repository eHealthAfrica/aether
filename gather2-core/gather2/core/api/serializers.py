# -*- coding: utf-8 -*-
from rest_framework import serializers

from . import models
from . import utils


class ProjectSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='project-detail',
        read_only=True,
        lookup_field='name'
    )
    mappings_url = serializers.HyperlinkedIdentityField(
        view_name='project_mapping-list',
        read_only=True,
        lookup_field='name',
        lookup_url_kwarg='parent_lookup_project__name',
    )
    projectschemas_url = serializers.HyperlinkedIdentityField(
        view_name='project_projectschema-list',
        read_only=True,
        lookup_url_kwarg='parent_lookup_project__name',
        lookup_field='name',
    )

    class Meta:
        model = models.Project
        fields = '__all__'


class MappingSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='mapping-detail',
        read_only=True
    )
    project_url = serializers.HyperlinkedRelatedField(
        view_name='project-detail',
        source='project',
        read_only=True,
        lookup_field='name',
    )
    responses_url = serializers.HyperlinkedIdentityField(
        view_name='mapping_response-list',
        read_only=True,
        lookup_url_kwarg='parent_lookup_mapping'
    )

    class Meta:
        model = models.Mapping
        fields = '__all__'


class ResponseSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='response-detail',
        read_only=True
    )
    mapping_url = serializers.HyperlinkedRelatedField(
        view_name='mapping-detail',
        source='mapping',
        read_only=True,
    )
    entities_url = serializers.HyperlinkedIdentityField(
        view_name='response_entity-list',
        read_only=True,
        lookup_url_kwarg='parent_lookup_response'
    )

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
                    map_revision=validated_data.pop('map_revision'),
                    payload=validated_data.pop('payload'),
                )
            else:
                response = models.Response(
                    payload=validated_data.pop('payload')
                )
            # Save the response to the db
            response.save()

        return response

    class Meta:
        model = models.Response
        fields = '__all__'


class SchemaSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='schema-detail',
        read_only=True
    )
    projectschemas_url = serializers.HyperlinkedIdentityField(
        view_name='schema_projectschema-list',
        read_only=True,
        lookup_url_kwarg='parent_lookup_schema',
    )

    class Meta:
        model = models.Schema
        fields = '__all__'


class ProjectSchemaSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='projectschema-detail',
        read_only=True
    )
    project_url = serializers.HyperlinkedRelatedField(
        view_name='project-detail',
        source='project',
        read_only=True,
        lookup_field='name',
    )
    schema_url = serializers.HyperlinkedRelatedField(
        view_name='schema-detail',
        source='schema',
        read_only=True,
    )
    entities_url = serializers.HyperlinkedIdentityField(
        view_name='projectschema_entity-list',
        read_only=True,
        lookup_url_kwarg='parent_lookup_projectschema',
    )

    class Meta:
        model = models.ProjectSchema
        fields = '__all__'


class EntitySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='entity-detail',
        read_only=True
    )
    projectschema_url = serializers.HyperlinkedRelatedField(
        view_name='projectschema-detail',
        source='projectschema',
        read_only=True,
    )

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

    class Meta:
        model = models.Entity
        fields = '__all__'
