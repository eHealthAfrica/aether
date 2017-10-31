# -*- coding: utf-8 -*-
from rest_framework import serializers

from . import models
from . import utils


class ProjectSerializer(serializers.ModelSerializer):

    url = serializers.HyperlinkedIdentityField('project-detail', read_only=True)

    mappings_url = serializers.HyperlinkedIdentityField(
        'project_mapping-list',
        read_only=True,
        lookup_url_kwarg='parent_lookup_project'
    )
    projectschemas_url = serializers.HyperlinkedIdentityField(
        'project_projectschema-list',
        read_only=True,
        lookup_url_kwarg='parent_lookup_project'
    )

    class Meta:
        model = models.Project
        fields = '__all__'


class MappingSerializer(serializers.ModelSerializer):

    url = serializers.HyperlinkedIdentityField('mapping-detail', read_only=True)

    project_url = serializers.HyperlinkedRelatedField(
        view_name='project-detail',
        source='project',
        read_only=True
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
            response = models.Response(
                revision=validated_data.pop('revision'),
                payload=validated_data.pop('payload'),
                mapping=validated_data.pop('mapping')
            )

            # Get the mapping definition from the response (response.mapping.definition):
            mapping_definition = response.mapping.definition

            # Get the primary key of the projectschema
            entity_pks = list(mapping_definition['entities'].values())

            # Get the schema of the projectschema
            project_schema = models.ProjectSchema.objects.get(pk=entity_pks[0])
            schema = project_schema.schema.definition

            # Get entity definitions
            entities = utils.get_entity_definitions(mapping_definition, schema)

            # Get field mappings
            field_mappings = utils.get_field_mappings(mapping_definition)

            # Get entity requirements
            requirements = utils.get_entity_requirements(entities, field_mappings)

            response_data = response.payload
            data, entities = utils.extract_entity(requirements, response_data, entities)

            entities_payload = list(entities.values())

            entity_list = []
            for payload in entities_payload[0]:
                entity = {
                    'revision': 'rev 1',
                    'payload': payload,
                    'status': 'Publishable',
                    'projectschema': project_schema
                }
                entity_list.append(entity)

            # Extract entities from response data (response.payload)

            # Save the response to the db
            response.save()

            # If extraction successful, create new entities

            if entity_list:
                for e in entity_list:
                    entity = models.Entity(
                        revision=e['revision'],
                        payload=e['payload'],
                        status=e['status'],
                        projectschema=e['projectschema'],
                        response=response
                    )
                    entity.save()
        else:
            response = models.Response(
                revision=validated_data.pop('revision'),
                payload=validated_data.pop('payload'),
            )
            # Save the response to the db
            response.save()

        return response

    url = serializers.HyperlinkedIdentityField('response-detail', read_only=True)

    mapping_url = serializers.HyperlinkedRelatedField(
        'mapping-detail',
        source='mapping',
        read_only=True
    )

    class Meta:
        model = models.Response
        fields = '__all__'


class SchemaSerializer(serializers.ModelSerializer):

    url = serializers.HyperlinkedIdentityField('schema-detail', read_only=True)
    projectschemas_url = serializers.HyperlinkedIdentityField(
        'schema_projectschema-list',
        read_only=True,
        lookup_url_kwarg='parent_lookup_schema'
    )

    class Meta:
        model = models.Schema
        fields = '__all__'


class ProjectSchemaSerializer(serializers.ModelSerializer):

    url = serializers.HyperlinkedIdentityField('projectschema-detail', read_only=True)
    project_url = serializers.HyperlinkedRelatedField(
        'project-detail',
        source='project',
        read_only=True
    )
    schema_url = serializers.HyperlinkedRelatedField(
        'schema-detail',
        source='schema',
        read_only=True
    )
    entities_url = serializers.HyperlinkedIdentityField(
        'projectschema_entity-list',
        read_only=True,
        lookup_url_kwarg='parent_lookup_projectschema'
    )

    class Meta:
        model = models.ProjectSchema
        fields = '__all__'


class EntitySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField('entity-detail', read_only=True)
    projectschema_url = serializers.HyperlinkedRelatedField(
        'projectschema-detail',
        source='projectschema',
        read_only=True
    )

    class Meta:
        model = models.Entity
        fields = '__all__'
