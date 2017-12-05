import os


def get_kernel_server_url():
    if os.environ.get('TESTING', '').lower() == 'true':
        return os.environ.get('AETHER_KERNEL_URL_TEST', '')
    else:
        return os.environ.get('AETHER_KERNEL_URL', '')


def get_mapping_responses_url(mapping_id, response_id=None):
    '''
    Returns Aether Kernel url to submit survey responses
    '''
    if mapping_id is None:
        raise Exception('Cannot get responses url without survey!')

    if not response_id:
        return '{kernel_url}/mappings/{mapping_id}/responses/'.format(
            kernel_url=get_kernel_server_url(),
            mapping_id=mapping_id,
        )
    else:
        return '{kernel_url}/mappings/{mapping_id}/responses/{response_id}/'.format(
            kernel_url=get_kernel_server_url(),
            mapping_id=mapping_id,
            response_id=response_id,
        )
