import os


def get_core_server_url():
    if os.environ.get('TESTING', '').lower() == 'true':
        return os.environ.get('AETHER_CORE_URL_TEST', '')
    else:
        return os.environ.get('AETHER_CORE_URL', '')


def get_survey_responses_url(mapping_id, response_id=None):
    '''
    Returns Aether Core url to submit survey responses
    '''
    if mapping_id is None:
        raise Exception('Cannot get responses url without survey!')

    if not response_id:
        return '{core_url}/mappings/{mapping_id}/responses/'.format(
            core_url=get_core_server_url(),
            mapping_id=mapping_id,
        )
    else:
        return '{core_url}/mappings/{mapping_id}/responses/{response_id}/'.format(
            core_url=get_core_server_url(),
            mapping_id=mapping_id,
            response_id=response_id,
        )
