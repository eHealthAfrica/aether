from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Response, calculate, MapResult, MapFunction
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Response, dispatch_uid='response_save')
def response_saved(sender, instance, **kwargs):
    response = instance

    for map_function in response.survey.mapfunction_set.all():
        print(map_function.code, response.data)

        # Calcualte the new results
        results, error = calculate(map_function.code, response.data)

        # Remove existing calculated data
        MapResult.objects.filter(map_function=map_function, response=response).delete()

        # Save new data
        for result in results:
            MapResult.objects.create(map_function=map_function, response=response, data=results)


@receiver(post_save, sender=MapFunction, dispatch_uid='map_function_save')
def map_function_saved(sender, instance, **kwargs):
    map_function = instance

    for response in map_function.survey.response_set.all():
        print(map_function.code, response.data)

        # Calcualte the new results
        results, error = calculate(map_function.code, response.data)

        # Remove existing calculated data
        MapResult.objects.filter(map_function=map_function, response=response).delete()

        # Save new data
        for result in results:
            MapResult.objects.create(map_function=map_function, response=response, data=results)
