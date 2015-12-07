from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Response, calculate, MapResult, MapFunction, ReduceFunction
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Response, dispatch_uid='response_save')
def response_saved(sender, instance, **kwargs):
    response = instance

    for map_function in response.survey.mapfunction_set.all():

        # Calcualte the new results
        results, error = calculate(map_function.code, response.data)

        # Remove existing calculated data
        MapResult.objects.filter(map_function=map_function, response=response).delete()

        # Save new data
        for result in results:
            MapResult.objects.create(
                map_function=map_function,
                response=response,
                output=error or "",
                data=result or "")

        for reduce_function in map_function.reducefunction_set.all():
            results, error = calculate(reduce_function.code, map_function.mapresult_set.all().values_list('data', flat=True))
            reduce_function.data = results
            reduce_function.output = error or ""
            reduce_function.save()


@receiver(post_save, sender=MapFunction, dispatch_uid='map_function_save')
def map_function_saved(sender, instance, **kwargs):
    map_function = instance

    for response in map_function.survey.response_set.all():

        # Calcualte the new results
        results, error = calculate(map_function.code, response.data)

        # Remove existing calculated data
        MapResult.objects.filter(map_function=map_function, response=response).delete()

        # Save new data
        for result in results:
            MapResult.objects.create(
                map_function=map_function,
                response=response,
                output=error or "",
                data=result or "")

    for reduce_function in map_function.reducefunction_set.all():
        results, error = calculate(reduce_function.code, map_function.mapresult_set.all().values_list('data', flat=True))
        reduce_function.data = results
        reduce_function.output = error or ""
        reduce_function.save()


@receiver(pre_save, sender=ReduceFunction, dispatch_uid='reduce_function_save')
def reduce_function_saved(sender, instance, **kwargs):
    reduce_function = instance
    results, error = calculate(reduce_function.code, reduce_function.map_function.mapresult_set.all().values_list('data', flat=True))
    reduce_function.data = results
    reduce_function.output = error or ""
