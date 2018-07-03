from django.contrib.auth import get_user_model
from django.test import TestCase

from ..ui_tags import get_fullname


class UiTagsTests(TestCase):

    def test_get_fullname(self):
        user = get_user_model().objects.create()

        self.assertEqual(get_fullname(user), '')
        self.assertEqual(get_fullname(user), str(user))
        self.assertEqual(get_fullname(user), user.username)

        user.username = 'user-name'
        self.assertEqual(get_fullname(user), str(user))
        self.assertEqual(get_fullname(user), user.username)

        user.first_name = 'first'
        user.last_name = ''
        self.assertEqual(get_fullname(user), user.username)

        user.first_name = ''
        user.last_name = 'last'
        self.assertEqual(get_fullname(user), user.username)

        user.first_name = 'first'
        user.last_name = 'last'
        self.assertEqual(get_fullname(user), 'first last')
