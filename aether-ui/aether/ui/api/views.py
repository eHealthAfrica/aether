from django.shortcuts import get_object_or_404
from django.utils import timezone

from http import HTTPStatus

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import models, serializers, utils


class PipelineViewSet(viewsets.ModelViewSet):
    queryset = models.Pipeline.objects.all()
    serializer_class = serializers.PipelineSerializer
    ordering = ('name',)

    @action(methods=['post'], detail=False)
    def fetch(self, request):
        '''
        This view gets kernel objects, transforms and loads into a pipeline
        '''
        try:
            utils.kernel_to_pipeline()
            pipelines = models.Pipeline.objects.all()
            serialized_data = serializers.PipelineSerializer(pipelines, context={'request': request}, many=True).data
            return Response(serialized_data, status=HTTPStatus.OK)
        except Exception as e:
            return Response(e)

    @action(methods=['post'], detail=True)
    def publish(self, request, pk=None):
        '''
        This view transform the supplied pipeline to kernal models,
        publish and update the pipeline with related kernel model ids.
        '''
        project_name = request.data.get('project_name', 'Aux')
        overwrite = request.data.get('overwrite', False)
        outcome = {
            'successful': [],
            'error': [],
            'exists': []
        }
        try:
            pipeline = get_object_or_404(models.Pipeline, pk=pk)
        except Exception as e:
            outcome['error'].append(str(e))
            return Response(outcome, status=HTTPStatus.BAD_REQUEST)
        outcome = utils.publish_preflight(pipeline, project_name, outcome)

        if outcome['error']:
            return Response(outcome, status=HTTPStatus.BAD_REQUEST)
        if outcome['exists']:
            if overwrite:
                outcome = utils.publish_pipeline(pipeline, project_name, True)
            else:
                return Response(outcome, status=HTTPStatus.BAD_REQUEST)
        else:
            outcome = utils.publish_pipeline(pipeline, project_name)

        if outcome['error']:
            return Response(outcome, status=HTTPStatus.BAD_REQUEST)
        else:
            pipeline.published_on = timezone.now()
            pipeline.save()
            serialized_data = serializers.PipelineSerializer(pipeline, context={'request': request}).data
            outcome['pipeline'] = serialized_data
            return Response(outcome, status=HTTPStatus.OK)
