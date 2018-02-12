from django.db.models import Count, Min, Max
from rest_framework import viewsets, permissions
from drf_openapi.views import SchemaView
from rest_framework.response import Response
from http import HTTPStatus

from . import models, serializers, filters


def get_entity_linked_data(entity, request, depth, start_depth=0):
    schema_definition_fields = entity.projectschema.schema.definition['fields']
    jsonld_fields = [item for item in schema_definition_fields if item.get('jsonldPredicate')]
    for item in jsonld_fields:
        try:
            if item['jsonldPredicate'].get('_id'):
                linked_data_ref = entity.payload.get(item['name'])
                linked_entity = models.Entity.objects.filter(payload__id=linked_data_ref)
                entity.payload[item['name']+'_data'] = serializers.EntitySerializer(
                    linked_entity, many=True, context={'request': request}).data[0]
                while (start_depth < depth):
                    start_depth = start_depth + 1
                    entity.payload[item['name']+'_data'] = serializers.EntitySerializer(
                        get_entity_linked_data(linked_entity.first(), request, start_depth),
                        context={'request': request}).data
                    Response('' + start_depth)
        except Exception as e:
            pass
    return entity


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = models.Project.objects.all()
    serializer_class = serializers.ProjectSerializer
    filter_class = filters.ProjectFilter


class MappingViewSet(viewsets.ModelViewSet):
    queryset = models.Mapping.objects.all()
    serializer_class = serializers.MappingSerializer
    filter_class = filters.MappingFilter


class MappingStatsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Mapping \
                     .objects \
                     .values('id', 'name', 'created', 'definition') \
                     .annotate(
                         first_submission=Min('submissions__created'),
                         last_submission=Max('submissions__created'),
                         submission_count=Count('submissions__id'),
                     )
    serializer_class = serializers.MappingStatsSerializer

    search_fields = ('name',)
    ordering_fields = ('name', 'created',)
    ordering = ('name',)


class SubmissionViewSet(viewsets.ModelViewSet):
    queryset = models.Submission.objects.all()
    serializer_class = serializers.SubmissionSerializer
    filter_class = filters.SubmissionFilter


class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = models.Attachment.objects.all()
    serializer_class = serializers.AttachmentSerializer
    filter_class = filters.AttachmentFilter


class SchemaViewSet(viewsets.ModelViewSet):
    queryset = models.Schema.objects.all()
    serializer_class = serializers.SchemaSerializer
    filter_class = filters.SchemaFilter


class ProjectSchemaViewSet(viewsets.ModelViewSet):
    queryset = models.ProjectSchema.objects.all()
    serializer_class = serializers.ProjectSchemaSerializer
    filter_class = filters.ProjectSchemaFilter


class EntityViewSet(viewsets.ModelViewSet):
    queryset = models.Entity.objects.all()
    serializer_class = serializers.EntitySerializer
    filter_class = filters.EntityFilter

    def retrieve(self, request, pk=None):
        try:
            selected_record = models.Entity.objects.get(pk=pk)
        except Exception as e:
            return Response(str(e), status=HTTPStatus.NOT_FOUND)
        include_linked_data = request.GET.get('include_linked_data')
        if include_linked_data == 'true':
            depth = request.GET.get('depth')
            if depth:
                depth = int(depth)
            else:
                depth = 1
            selected_record = get_entity_linked_data(selected_record, request, depth)
        serializer_class = serializers.EntitySerializer(selected_record, context={'request': request})
        return Response(serializer_class.data, status=HTTPStatus.OK)


class AetherSchemaView(SchemaView):
    permission_classes = (permissions.AllowAny, )
