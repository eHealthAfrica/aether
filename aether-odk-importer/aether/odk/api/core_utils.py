import os


def get_kernel_server_url():
    if os.environ.get('TESTING', '').lower() == 'true':
        return os.environ.get('AETHER_KERNEL_URL_TEST', '')
    else:
        return os.environ.get('AETHER_KERNEL_URL', '')


def get_mapping_submissions_url(mapping_id, submission_id=None):
    '''
    Returns Aether Kernel url to make mapping submissions
    '''
    if mapping_id is None:
        raise Exception('Cannot get submissions url without mapping!')

    if not submission_id:
        return '{kernel_url}/mappings/{mapping_id}/submissions/'.format(
            kernel_url=get_kernel_server_url(),
            mapping_id=mapping_id,
        )
    else:
        return '{kernel_url}/mappings/{mapping_id}/submissions/{submission_id}/'.format(
            kernel_url=get_kernel_server_url(),
            mapping_id=mapping_id,
            submission_id=submission_id,
        )
