import string
import json

from django.utils.safestring import mark_safe

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import JsonLexer
from pygments.lexers.python import Python3Lexer


def __prettified__(response, lexer):
    # Truncate the data. Alter as needed
    response = response[:5000]
    # Get the Pygments formatter
    formatter = HtmlFormatter(style='colorful')
    # Highlight the data
    response = highlight(response, lexer, formatter)
    # Get the stylesheet
    style = '<style>' + formatter.get_style_defs() + '</style>'
    # Safe the output
    return mark_safe(style + response)


def json_prettified(value, indent=2):
    '''
    Function to display pretty version of our json data
    https://www.pydanny.com/pretty-formatting-json-django-admin.html
    '''
    return __prettified__(json.dumps(value, sort_keys=True, indent=indent), JsonLexer())


def code_prettified(value):
    '''
    Function to display pretty version of our code data
    '''
    return __prettified__(value, Python3Lexer())


def json_printable(obj):
    # Note: a combinations of JSONB in postgres and json parsing gives a nasty db error
    # See: https://bugs.python.org/issue10976#msg159391
    # and
    # http://www.postgresql.org/message-id/E1YHHV8-00032A-Em@gemulon.postgresql.org
    if isinstance(obj, dict):
        return {json_printable(k): json_printable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [json_printable(elem) for elem in obj]
    elif isinstance(obj, str):
        # Only printables
        return ''.join(x for x in obj if x in string.printable)
    else:
        return obj
