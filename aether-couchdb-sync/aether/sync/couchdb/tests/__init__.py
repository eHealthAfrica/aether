from django.test import TestCase
from uuid import uuid4

from .. import api


class CouchDBTestCase(TestCase):
    test_db = 'test-' + str(uuid4())

    def setUp(self):
        r = api.get(self.test_db)
        if r.status_code == 404:
            api.put(self.test_db)

    def tearDown(self):
        r = api.get(self.test_db)
        if r.status_code != 404:
            api.delete(self.test_db)
