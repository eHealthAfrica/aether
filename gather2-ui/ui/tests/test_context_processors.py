from django.test import RequestFactory, TestCase

from ..context_processors import gather2


class ContextProcessorsTests(TestCase):

    def test_gather2(self):
        request = RequestFactory().get('/')

        self.assertEqual(gather2(request), {
            'dev_mode': False,
            'app_name': 'Gather',
            'org_name': 'eHealth Africa (Dev mode)',
        })
