import os


def get_core_server_url():
    if os.environ.get('TESTING', '').lower() == 'true':
        return os.environ.get('GATHER_CORE_URL_TEST', '')
    else:
        return os.environ.get('GATHER_CORE_URL', '')


def get_mapping_submissions_url(mapping_id, submission_id=None):
    '''
    Returns Gather2 Core url to make mapping submissions
    '''
    if mapping_id is None:
        raise Exception('Cannot get submissions url without mapping!')

    if not submission_id:
        return '{core_url}/mappings/{mapping_id}/submissions/'.format(
            core_url=get_core_server_url(),
            mapping_id=mapping_id,
        )
    else:
        return '{core_url}/mappings/{mapping_id}/submissions/{submission_id}/'.format(
            core_url=get_core_server_url(),
            mapping_id=mapping_id,
            submission_id=submission_id,
        )
