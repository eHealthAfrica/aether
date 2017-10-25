from django.test import TestCase
from .. import utils


class UtilsTests(TestCase):

    def test_json_prettified_simple(self):
        data = {}
        expected = '<pre><span></span><span class="p">{}</span>\n</pre>'
        pretty = str(utils.json_prettified(data))
        self.assertTrue(expected in pretty, pretty)

    def test_code_prettified_simple(self):
        data = 'print "Hello world!"'
        expected = '<span class="s2">&quot;Hello world!&quot;</span>'

        pretty = str(utils.code_prettified(data))
        self.assertTrue(expected in pretty, pretty)
