import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import MapFunction, MapResult, ReduceFunction, Response, calculate

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Response, dispatch_uid='response_save')
def response_saved(sender, instance, **kwargs):
    response = instance

    for map_function in response.survey.mapfunction_set.all():

        # Calcualte the new output
        outputs, error = calculate(map_function.code, response.data)

        # Remove existing calculated data
        MapResult.objects.filter(
            map_function=map_function, response=response).delete()

        # Save new data
        for output in outputs:
            MapResult.objects.create(
                map_function=map_function,
                response=response,
                output=output or "",
                error=error or "")

        for reduce_function in map_function.reducefunction_set.all():
            code = reduce_function.code
            data = map_function.mapresult_set.all().values_list('output', flat=True)
            out, err = calculate(code, data)
            reduce_function.output = out
            reduce_function.error = err or ""
            reduce_function.save()


@receiver(post_save, sender=MapFunction, dispatch_uid='map_function_save')
def map_function_saved(sender, instance, **kwargs):
    map_function = instance

    for response in map_function.survey.response_set.all():

        # Calcualte the new results
        outputs, err = calculate(map_function.code, response.data)

        # Remove existing calculated data
        MapResult.objects.filter(
            map_function=map_function, response=response).delete()

        # Save new data
        for output in outputs:
            MapResult.objects.create(
                map_function=map_function,
                response=response,
                output=output or "",
                error=err or "")

    for reduce_function in map_function.reducefunction_set.all():
        code = reduce_function.code
        data = map_function.mapresult_set.all().values_list('output', flat=True)
        out, err = calculate(code, data)
        reduce_function.output = out
        reduce_function.error = err or ""
        reduce_function.save()


@receiver(pre_save, sender=ReduceFunction, dispatch_uid='reduce_function_save')
def reduce_function_saved(sender, instance, **kwargs):
    reduce_function = instance
    outputs, error = calculate(reduce_function.code, list(
        reduce_function.map_function.mapresult_set.all().values_list('output', flat=True)))
    reduce_function.output = outputs
    reduce_function.error = error or ""
