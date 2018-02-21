from django.db.models import Count, Min, Max
from rest_framework import viewsets, permissions
from rest_framework.decorators import detail_route, list_route
from drf_openapi.views import SchemaView

from . import models, serializers, filters


class CustomViewSet(viewsets.ModelViewSet):

    @detail_route(methods=['get', 'post'])
    def details(self, request, pk=None, *args, **kwargs):
        '''
        Allow to retrieve data from a POST request.
        Reachable at ``.../{model}/{pk}/details/``
        '''

        return self.retrieve(request, pk, *args, **kwargs)

    @list_route(methods=['get', 'post'])
    def fetch(self, request, *args, **kwargs):
        '''
        Allow to list data from a POST request.
        Reachable at ``.../{model}/fetch/``
        '''

        return self.list(request, *args, **kwargs)


class ProjectViewSet(CustomViewSet):
    queryset = models.Project.objects.all()
    serializer_class = serializers.ProjectSerializer
    filter_class = filters.ProjectFilter


class MappingViewSet(CustomViewSet):
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


class SubmissionViewSet(CustomViewSet):
    queryset = models.Submission.objects.all()
    serializer_class = serializers.SubmissionSerializer
    filter_class = filters.SubmissionFilter


class AttachmentViewSet(CustomViewSet):
    queryset = models.Attachment.objects.all()
    serializer_class = serializers.AttachmentSerializer
    filter_class = filters.AttachmentFilter


class SchemaViewSet(CustomViewSet):
    queryset = models.Schema.objects.all()
    serializer_class = serializers.SchemaSerializer
    filter_class = filters.SchemaFilter


class ProjectSchemaViewSet(CustomViewSet):
    queryset = models.ProjectSchema.objects.all()
    serializer_class = serializers.ProjectSchemaSerializer
    filter_class = filters.ProjectSchemaFilter


class EntityViewSet(CustomViewSet):
    queryset = models.Entity.objects.all()
    serializer_class = serializers.EntitySerializer
    filter_class = filters.EntityFilter


class AetherSchemaView(SchemaView):
    permission_classes = (permissions.AllowAny, )
