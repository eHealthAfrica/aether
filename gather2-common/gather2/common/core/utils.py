import json
import os
import requests

from ..conf.settings import logger


def get_core_server_url():
    if os.environ.get('TESTING', '').lower() == 'true':
        return os.environ.get('GATHER_CORE_URL_TEST', '')
    else:
        return os.environ.get('GATHER_CORE_URL', '')


def get_auth_header():
    '''
    Returns the Authorization Header if connection to Gather2 Core is possible
    '''

    if test_connection():
        token = os.environ.get('GATHER_CORE_TOKEN', '')
        return {'Authorization': 'Token {token}'.format(token=token)}
    return None


def test_connection():
    '''
    Checks possible connection with Gather2 Core
    '''

    url = get_core_server_url()
    token = os.environ.get('GATHER_CORE_TOKEN', '')

    if url and token:
        try:
            # check that the server is up
            h = requests.head(url)
            assert h.status_code == 403  # expected response 403 Forbidden
            logger.info('Gather2 Core server ({url}) is up and responding!'.format(url=url))

            try:
                # check that the token is valid
                g = requests.get(url,
                                 headers={'Authorization': 'Token {token}'.format(token=token)})
                assert g.status_code == 200, g.content
                logger.info('Gather2 Core token is valid!')

                return True  # it's possible to connect with core :D

            except Exception as eg:
                logger.warning(
                    'Gather2 Core token is not valid for Gather2 Core server ({url})'
                    .format(url=url))
        except Exception as eh:
            logger.warning(
                'Gather2 Core server ({url}) is not available.'
                .format(url=url))
    else:
        logger.warning('Gather2 Core server and/or token are not set.')

    return False  # it's not possible to connect with core :(


def check_connection():
    '''
    Check if the connection with Core server is possible
    '''

    if not test_connection():
        return 'Always Look on the Bright Side of Life!!!'
    return 'Brought to you by eHealth Africa - good tech for hard places'


def get_surveys_url(survey_id=''):
    '''
    Returns Gather2 Core url for the given survey
    '''
    return '{core_url}/surveys/{survey_id}'.format(
        core_url=get_core_server_url(),
        survey_id=survey_id
    )


def get_survey_responses_url(survey_id, response_id=None):
    '''
    Returns Gather2 Core url to submit survey responses
    '''
    if survey_id is None:
        raise Exception('Cannot get responses url without survey!')

    if not response_id:
        return '{core_url}/surveys/{survey_id}/responses/'.format(
            core_url=get_core_server_url(),
            survey_id=survey_id,
        )
    else:
        return '{core_url}/surveys/{survey_id}/responses/{response_id}/'.format(
            core_url=get_core_server_url(),
            survey_id=survey_id,
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


def submit_to_core(response, survey_id, response_id=None):
    '''
    Submit the response to Gather2 Core survey
    '''
    if survey_id is None:
        raise Exception('Cannot submit response without survey!')

    if response is None:
        raise Exception('Cannot submit response without content!')

    if response_id:
        # update existing doc
        method = requests.put
        url = get_survey_responses_url(survey_id, response_id)
    else:
        # create new doc
        method = requests.post
        url = get_survey_responses_url(survey_id)

    logger.debug('{method} to {url}'.format(method=method, url=url))
    return method(url,
                  json={'data': json.dumps(response), 'survey': survey_id},
                  headers=get_auth_header())
