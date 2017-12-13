# -*- coding: utf-8 -*-
from rest_framework import serializers

from . import models
from . import utils

from six import StringIO
import ruamel.yaml as yaml
import schema_salad.schema as SchemaSaladSchema


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

    schemas_url = serializers.HyperlinkedIdentityField(
        view_name='project_schema-list',
        read_only=True,
        lookup_url_kwarg='parent_lookup_project__name',
        lookup_field='name',
    )

    def create(self, validated_data):
        try:
            project = models.Project(
                revision=validated_data.pop('revision'),
                name=validated_data.pop('name'),
                salad_schema=validated_data.pop('salad_schema'),
                jsonld_context=validated_data.pop('jsonld_context'),
                rdf_definition=validated_data.pop('rdf_definition')
            )
            project.save()
            if '$graph' in project.salad_schema:
                text = str(project.salad_schema['$graph'])
                textIO = StringIO(text)
                result = yaml.round_trip_load(textIO)
                avsc_obj = SchemaSaladSchema.make_avro_schema(result, utils.loader)[1]

                for avro_schema in avsc_obj:
                    generated_schema = models.Schema(
                        name=avro_schema['name'],
                        type=avro_schema['type'],
                        definition=avro_schema,
                        project=project
                    )
                    generated_schema.save()
            else:
                raise Exception('Invalid salad schema')

            return project
        except Exception as e:
            raise serializers.ValidationError({
                'description': 'Project validation failed: {}'.format(e)
            })

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
    submissions_url = serializers.HyperlinkedIdentityField(
        view_name='mapping_submission-list',
        read_only=True,
        lookup_url_kwarg='parent_lookup_mapping'
    )

    class Meta:
        model = models.Mapping
        fields = '__all__'


class SubmissionSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='submission-detail',
        read_only=True
    )
    mapping_url = serializers.HyperlinkedRelatedField(
        view_name='mapping-detail',
        source='mapping',
        read_only=True,
    )
    entities_url = serializers.HyperlinkedIdentityField(
        view_name='submission_entity-list',
        read_only=True,
        lookup_url_kwarg='parent_lookup_submission'
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


class SchemaSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='schema-detail',
        read_only=True,
        lookup_field='name',
    )
    projectschemas_url = serializers.HyperlinkedIdentityField(
        view_name='schema_projectschema-list',
        read_only=True,
        lookup_url_kwarg='parent_lookup_schema__name',
        lookup_field='name',
    )
    project_url = serializers.HyperlinkedRelatedField(
        view_name='project-detail',
        source='project',
        read_only=True,
        lookup_field='name',
    )

    class Meta:
        model = models.Schema
        fields = '__all__'


class ProjectSchemaSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='projectschema-detail',
        read_only=True,
        lookup_field='name',
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
        lookup_field='name',
    )
    entities_url = serializers.HyperlinkedIdentityField(
        view_name='projectschema_entity-list',
        read_only=True,
        lookup_url_kwarg='parent_lookup_projectschema__name',
        lookup_field='name',
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
        lookup_field='name',
    )

    def create(self, validated_data):
        entity = models.Entity(
            payload=validated_data.pop('payload'),
            status=validated_data.pop('status'),
            projectschema=validated_data.pop('projectschema'),
        )
        if "submission" in validated_data:
            entity.submission = validated_data.pop('submission')
        if 'id' in validated_data:
            entity.id = validated_data.pop('id')
        entity.payload['_id'] = str(entity.id)
        entity.save()
        return entity

    class Meta:
        model = models.Entity
        fields = '__all__'
