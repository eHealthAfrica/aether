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
    # lookup_field = 'name'

    # def get_object(self):
    #     if self.request.method == 'PUT':
    #         mapping = models.Mapping.objects.filter(name=self.kwargs.get('name')).first()
    #         if mapping:
    #             return mapping
    #         else:
    #             return models.Mapping(name=self.kwargs.get('name'))
    #     else:
    #         return super(MappingViewSet, self).get_object()


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


class EntityViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = models.Entity.objects.all()
    serializer_class = serializers.EntitySerializer
