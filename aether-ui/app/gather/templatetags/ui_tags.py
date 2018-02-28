from django import template


register = template.Library()


@register.filter(name='get_fullname')
def get_fullname(user):
    '''
    Returns a readable name of the user.
    - ``first_name`` + ``last_name``
    - ``name``
    - ``username``
    '''

    if user.first_name and user.last_name:
        return '{} {}'. format(user.first_name, user.last_name)

    return user.username


@register.filter(name='get_token')
def get_app_token(user, app_name):
    '''
    Returns a token to connect to the given app
    '''

    return user.app_tokens.get_app_token(app_name)
