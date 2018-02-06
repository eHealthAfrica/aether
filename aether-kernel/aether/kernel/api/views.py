from django.db.models import Count, Min, Max
from rest_framework import viewsets, permissions
from drf_openapi.views import SchemaView
from rest_framework.response import Response
from http import HTTPStatus

from . import models, serializers, filters


def aether_retrieve(request, model, serializer, pk=None):
    selected_record = model.objects.get(pk=pk)
    all_versions = request.GET.get('all_versions')
    if all_versions == 'true':
        queryset = model.objects.filter(_id=selected_record._id)\
            .order_by('-modified')
        serializer_class = serializer(queryset,\
        many=True, context={'request': request})
        return Response(serializer_class.data, status=HTTPStatus.OK)
    serializer_class = serializer(selected_record,\
        context={'request': request})
    return Response(serializer_class.data, status=HTTPStatus.OK)

def aether_list(request, model, serializer):
    queryset = model.objects.filter(deleted=False)\
        .order_by('_id', '-modified').distinct('_id')
    serializer_class = serializer(queryset,\
        many=True, context={'request': request})
    return Response(serializer_class.data, status=HTTPStatus.OK)

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = models.Project.objects.all()
    serializer_class = serializers.ProjectSerializer
    filter_class = filters.ProjectFilter

    def list(self, request):
        return aether_list(request, models.Project, serializers.ProjectSerializer)

    def retrieve(self, request, pk=None):
       return aether_retrieve(request, models.Project, serializers.ProjectSerializer, pk)



class MappingViewSet(viewsets.ModelViewSet):
    queryset = models.Mapping.objects.all()
    serializer_class = serializers.MappingSerializer
    filter_class = filters.MappingFilter

    def list(self, request):
        return aether_list(request, models.Mapping, serializers.MappingSerializer)

    def retrieve(self, request, pk=None):
       return aether_retrieve(request, models.Mapping, serializers.MappingSerializer, pk)
        


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

    def list(self, request):
        return aether_list(request, models.Submission, serializers.SubmissionSerializer)

    def retrieve(self, request, pk=None):
       return aether_retrieve(request, models.Submission, serializers.SubmissionSerializer, pk)


class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = models.Attachment.objects.all()
    serializer_class = serializers.AttachmentSerializer
    filter_class = filters.AttachmentFilter

    def list(self, request):
        return aether_list(request, models.Attachment, serializers.AttachmentSerializer)

    def retrieve(self, request, pk=None):
       return aether_retrieve(request, models.Attachment, serializers.AttachmentSerializer, pk)


class SchemaViewSet(viewsets.ModelViewSet):
    queryset = models.Schema.objects.all()
    serializer_class = serializers.SchemaSerializer
    filter_class = filters.SchemaFilter

    def list(self, request):
        return aether_list(request, models.Schema, serializers.SchemaSerializer)

    def retrieve(self, request, pk=None):
       return aether_retrieve(request, models.Schema, serializers.SchemaSerializer, pk)


class ProjectSchemaViewSet(viewsets.ModelViewSet):
    queryset = models.ProjectSchema.objects.all()
    serializer_class = serializers.ProjectSchemaSerializer
    filter_class = filters.ProjectSchemaFilter

    def list(self, request):
        return aether_list(request, models.ProjectSchema, serializers.ProjectSchemaSerializer)

    def retrieve(self, request, pk=None):
       return aether_retrieve(request, models.ProjectSchema, serializers.ProjectSchemaSerializer, pk)

class EntityViewSet(viewsets.ModelViewSet):
    queryset = models.Entity.objects.all()
    serializer_class = serializers.EntitySerializer
    filter_class = filters.EntityFilter

    def list(self, request):
        return aether_list(request, models.Entity, serializers.EntitySerializer)

    def retrieve(self, request, pk=None):
       return aether_retrieve(request, models.Entity, serializers.EntitySerializer, pk)


class AetherSchemaView(SchemaView):
    permission_classes = (permissions.AllowAny, )
