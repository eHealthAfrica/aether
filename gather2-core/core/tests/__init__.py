
EXAMPLE_SCHEMA = {
    'title': 'Example Schema',
    'type': 'object',
    'properties': {
        'firstName': {
            'type': 'string'
        },
        'lastName': {
            'type': 'string'
        },
        'age': {
            'description': 'Age',
            'type': 'integer',
            'minimum': 0
        }
    },
    'required': ['firstName', 'lastName']
}

EXAMPLE_CODE_UNSAFE_1 = '''
import os
# it has no access to app variables but... it scares!!!
print os.environ.get('RDS_HOSTNAME')
'''

EXAMPLE_CODE_UNSAFE_2 = '''
import sys
print(sys.exc_info())
sys.exit(-1)
'''
