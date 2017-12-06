from rest_framework import viewsets, permissions
from rest_framework_extensions.mixins import NestedViewSetMixin
from drf_openapi.views import SchemaView


from . import models, serializers


class ProjectViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = models.Project.objects.all()
    serializer_class = serializers.ProjectSerializer
    lookup_field = 'name'


class MappingViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = models.Mapping.objects.all()
    serializer_class = serializers.MappingSerializer


class SubmissionViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = models.Submission.objects.all()
    serializer_class = serializers.SubmissionSerializer


class SchemaViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = models.Schema.objects.all()
    serializer_class = serializers.SchemaSerializer
    lookup_field = 'name'


class ProjectSchemaViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = models.ProjectSchema.objects.all()
    serializer_class = serializers.ProjectSchemaSerializer
    lookup_field = 'name'


class EntityViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = models.Entity.objects.all()
    serializer_class = serializers.EntitySerializer


class AetherSchemaView(SchemaView):
    permission_classes = (permissions.AllowAny, )
