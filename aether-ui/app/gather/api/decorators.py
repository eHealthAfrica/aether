from django.contrib.auth.decorators import user_passes_test

from ..settings import AETHER_APPS
from .models import UserTokens


def tokens_required(function=None, redirect_field_name=None, login_url=None):
    '''
    Decorator for views that checks that a user is logged in and
    he/she has valid tokens for each app used in the proxy view.
    '''

    def user_token_test(user):
        '''
        Checks for each external app that the user can currently connect to it.
        '''
        try:
            for app in AETHER_APPS:
                # checks if there is a valid token for this app
                if UserTokens.get_or_create_user_app_token(user, app) is None:
                    return False
            return True
        except Exception as e:
            return False

    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and user_token_test(u),
        login_url=login_url or '/~tokens',
        redirect_field_name=redirect_field_name,
    )
    if function:  # pragma: no cover
        return actual_decorator(function)
    return actual_decorator  # pragma: no cover
