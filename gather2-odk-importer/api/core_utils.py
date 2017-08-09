import os
import requests

from importer.settings import logger


def get_core_server_url():
    if os.environ.get('TESTING', '').lower() == 'true':
        return os.environ.get('GATHER_CORE_URL_TEST', '')
    else:
        return os.environ.get('GATHER_CORE_URL', '')


def get_auth_header():
    '''
    Returns Authorization Header if connection to Gather2 Core is possible
    '''

    if test_connection():
        token = os.environ.get('GATHER_CORE_TOKEN', '')
        return {'Authorization': 'Token {token}'.format(token=token)}
    return None


def test_connection():
    '''
    Checks possible connection with GATHER2 CORE
    '''

    url = get_core_server_url()
    token = os.environ.get('GATHER_CORE_TOKEN', '')
    err_msg = 'saving XForm responses will not work'

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
                    'Gather2 Core token is not valid for Gather2 Core server ({url}), {then}'
                    .format(url=url, then=err_msg))
        except Exception as eh:
            logger.warning(
                'Gather2 Core server ({url}) is not available, {then}.'
                .format(url=url, then=err_msg))
    else:
        logger.warning(
            'Gather2 Core server and/or token are not set, {then}.'
            .format(then=err_msg))

    return False  # it's not possible to connect with core :(


def get_surveys_url(survey_id=''):
    '''
    Returns Gather2 Core url to submit survey responses
    '''
    return '{core_url}/surveys/{survey_id}'.format(
        core_url=get_core_server_url(),
        survey_id=survey_id
    )


def get_survey_responses_url(survey_id, response_id=''):
    '''
    Returns Gather2 Core url to submit survey responses
    '''
    return '{core_url}/surveys/{survey_id}/responses/{response_id}'.format(
        core_url=get_core_server_url(),
        survey_id=survey_id,
        response_id=response_id,
    )
