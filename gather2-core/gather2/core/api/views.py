from rest_framework import viewsets
from rest_framework_extensions.mixins import NestedViewSetMixin

from . import models, serializers


class ProjectViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = models.Project.objects.all()
    serializer_class = serializers.ProjectSerializer
    lookup_field = 'name'


class MappingViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = models.Mapping.objects.all()
    serializer_class = serializers.MappingSerializer


class ResponseViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = models.Response.objects.all()
    serializer_class = serializers.ResponseSerializer


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
