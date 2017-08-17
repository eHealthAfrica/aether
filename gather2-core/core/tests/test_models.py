from django.contrib.auth import get_user_model
from django.test import TransactionTestCase

from .. import models


class ModelsTests(TransactionTestCase):

    def setUp(self):
        username = 'test'
        email = 'test@example.com'
        password = 'testtest'

        self.user = get_user_model().objects.create_user(username, email, password)

    def test_models(self):
        self.assertEquals(models.MapResult.objects.count(), 0)

        survey = models.Survey.objects.create(
            created_by=self.user,
            name='a name',
            schema={},
        )
        self.assertEquals(str(survey), survey.name)
        self.assertTrue(survey.schema_prettified is not None)

        response = models.Response.objects.create(
            created_by=self.user,
            data={'a': 1},
            survey=survey,
        )
        self.assertEquals(str(response), '{} - {}'.format(survey.name, response.id))
        self.assertTrue(response.data_prettified is not None)

        map_function = models.MapFunction.objects.create(
            code='print "Hello World!"',
            survey=survey,
        )
        self.assertEquals(str(map_function), '{} - {}'.format(survey.name, map_function.id))
        self.assertTrue(map_function.code_prettified is not None)

        # map result is generated automatically
        map_result = models.MapResult.objects.first()

        self.assertEquals(str(map_result), '{} - {}'.format(response, map_result.id))
        self.assertTrue(map_result.output is not None)
        self.assertEquals(map_result.output, 'Hello World!', map_result.output)
        self.assertEquals(map_result.error, '', map_result.error)
        self.assertTrue(map_result.output_prettified is not None)

        reduce_function = models.ReduceFunction.objects.create(
            code='print "Good bye!"',
            map_function=map_function,
        )
        self.assertEquals(str(reduce_function), '{} - {}'.format(map_function, reduce_function.id))
        self.assertTrue(reduce_function.code_prettified is not None)
        self.assertTrue(reduce_function.output is not None)
        self.assertEquals(reduce_function.output, ['Good bye!'], reduce_function.output)
        self.assertEquals(reduce_function.error, '', reduce_function.error)
        self.assertTrue(reduce_function.output_prettified is not None)
