from rest_framework import viewsets
from rest_framework_extensions.mixins import NestedViewSetMixin

from . import models, serializers


class ProjectViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = models.Project.objects.all()
    serializer_class = serializers.ProjectSerializer


class MappingViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = models.Mapping.objects.all()
    serializer_class = serializers.MappingSerializer

    def get_object(self):
        if self.request.method == 'PUT':
            mapping = models.Mapping.objects.filter(id=self.kwargs.get('pk')).first()
            if mapping:
                return mapping
            else:
                return models.Mapping(id=self.kwargs.get('pk'))
        else:
            return super(MappingViewSet, self).get_object()


class ResponseViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = models.Response.objects.all()
    serializer_class = serializers.ResponseSerializer


class SchemaViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = models.Schema.objects.all()
    serializer_class = serializers.SchemaSerializer


class ProjectSchemaViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = models.ProjectSchema.objects.all()
    serializer_class = serializers.ProjectSchemaSerializer


class EntityViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = models.Entity.objects.all()
    serializer_class = serializers.EntitySerializer
