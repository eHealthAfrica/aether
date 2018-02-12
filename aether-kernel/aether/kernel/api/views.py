from django.db.models import Count, Min, Max

from rest_framework import viewsets, permissions
from rest_framework.decorators import (
    api_view,
    permission_classes,
    renderer_classes,
)
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from drf_openapi.views import SchemaView

from . import (
    filters,
    mapping_validation,
    models,
    serializers,
    utils,
)


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


class AetherSchemaView(SchemaView):
    permission_classes = (permissions.AllowAny, )


@api_view(['POST'])
@renderer_classes([JSONRenderer])
@permission_classes([IsAuthenticated])
def validate_mappings(request):
    '''
    Given a `submission_payload`, a `mapping_definition` and a list of
    `entities`, verify that each mapping function in `mapping_definition` can
    extract a value from `submission_payload` and assign it to at least one
    entity in `entities`.

    This endpoint is useful for clients who are in the process of
    developing an Aether solution but have not yet submitted any complete
    Project; using this endpoint, it is possible to check the mapping functions
    (jsonpaths) align with both the source (`submission_payload`) and the
    target (`entity_list`).
    '''

    try:
        data = request.data
        entities = utils.extract_create_entities(**data)
        mapping_errors = mapping_validation.validate_mappings(
            submission_payload=data['submission_payload'],
            entity_list=entities,
            mapping_definition=data['mapping_definition'],
        )
        return Response({
            'entities': [
                entity.payload for entity in entities
            ],
            'mapping_errors': [
                error._asdict() for error in mapping_errors
            ],
        })
    except Exception as e:
        return Response(
            {'message': 'Entity extraction error'},
            status=status.HTTP_400_BAD_REQUEST
        )
