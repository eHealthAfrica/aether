import os
import requests

from ..conf.settings import logger


def get_kernel_server_url():
    if os.environ.get('TESTING', '').lower() == 'true':
        return os.environ.get('AETHER_KERNEL_URL_TEST', '')
    else:
        return os.environ.get('AETHER_KERNEL_URL', '')


def get_auth_header():
    '''
    Returns the Authorization Header if connection to Aether Kernel is possible
    '''

    if test_connection():
        token = os.environ.get('AETHER_KERNEL_TOKEN', '')
        return {'Authorization': 'Token {token}'.format(token=token)}
    return None


def test_connection():
    '''
    Checks possible connection with Aether Kernel
    '''

    url = get_kernel_server_url()
    token = os.environ.get('AETHER_KERNEL_TOKEN', '')

    if url and token:
        try:
            # check that the server is up
            h = requests.head(url)
            assert h.status_code == 403  # expected response 403 Forbidden
            logger.info('Aether Kernel server ({url}) is up and responding!'.format(url=url))

            try:
                # check that the token is valid
                g = requests.get(url,
                                 headers={'Authorization': 'Token {token}'.format(token=token)})
                assert g.status_code == 200, g.content
                logger.info('Aether Kernel token is valid!')

                return True  # it's possible to connect with kernel :D

            except Exception as eg:
                logger.warning(
                    'Aether Kernel token is not valid for Aether Kernel server ({url})'
                    .format(url=url))
        except Exception as eh:
            logger.warning(
                'Aether Kernel server ({url}) is not available.'
                .format(url=url))
    else:
        logger.warning('Aether Kernel server and/or token are not set.')

    return False  # it's not possible to connect with kernel :(


def check_connection():
    '''
    Check if the connection with Kernel server is possible
    '''

    if not test_connection():
        return 'Always Look on the Bright Side of Life!!!'
    return 'Brought to you by eHealth Africa - good tech for hard places'


def get_surveys_url(mapping_id=''):
    '''
    Returns Aether Kernel url for the given survey
    '''
    return '{kernel_url}/mappings/{mapping_id}'.format(
        kernel_url=get_kernel_server_url(),
        mapping_id=mapping_id
    )


def get_survey_responses_url(mapping_id, response_id=None):
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


def get_all_docs(url):
    '''
    Returns all documents linked to an url, even with pagination
    '''
    def get_data(url):
        resp = requests.get(url, headers=get_auth_header())
        resp.raise_for_status()
        return resp.json()

    data = get_data(url)
    results = data['results']
    while 'next' in data and data['next']:
        data = get_data(data['next'])
        results += data['results']

    return results


def submit_to_kernel(response, mapping_id, response_id=None):
    '''
    Submit the response to Aether Kernel survey
    '''
    if mapping_id is None:
        raise Exception('Cannot submit response without survey!')

    if response is None:
        raise Exception('Cannot submit response without content!')

    if response_id:
        # update existing doc
        method = requests.put
        url = get_survey_responses_url(mapping_id, response_id)
    else:
        # create new doc
        method = requests.post
        url = get_survey_responses_url(mapping_id)

    logger.debug('{method} to {url}'.format(method=method, url=url))
    return method(
        url,
        json={
            'payload': response,
            'survey': mapping_id
        },
        headers=get_auth_header(),
    )
