import logging
import os
import requests

logger = logging.getLogger(__name__)


def get_auth_header():
    '''
    Returns Authorization Header if connection to Gather2 Core is possible
    '''

    if test_connection():
        GATHER_CORE_TOKEN = os.environ.get('GATHER_CORE_TOKEN', '')
        return {'Authorization': 'Token {}'.format(GATHER_CORE_TOKEN)}
    return None


def test_connection():
    '''
    Checks possible connection with GATHER2 CORE
    '''

    GATHER_CORE_URL = os.environ.get('GATHER_CORE_URL', '')
    GATHER_CORE_TOKEN = os.environ.get('GATHER_CORE_TOKEN', '')
    fail_action = 'saving XForm responses will not work'

    if GATHER_CORE_URL and GATHER_CORE_TOKEN:
        GATHER_CORE_AUTH_HEADER = {'Authorization': 'Token {}'.format(GATHER_CORE_TOKEN)}
        try:
            # check that the server is up
            h = requests.head(GATHER_CORE_URL)
            assert h.status_code == 200
            logger.info('Gather2 Core server ({}) is up and responding!'.format(GATHER_CORE_URL))

            try:
                # check that the token is valid
                g = requests.get(GATHER_CORE_URL + '/surveys.json', headers=GATHER_CORE_AUTH_HEADER)
                assert g.status_code == 200, g.content
                logger.info('Gather2 Core token is valid!')

                return True  # it's possible to connect with core

            except Exception as eg:
                logger.exception(
                    'Gather2 Core token is not valid for Gather2 Core server ({}), {}'.format(
                        GATHER_CORE_URL, fail_action))
        except Exception as eh:
            logger.warning('Gather2 Core server ({}) is not available, {}.'.format(
                GATHER_CORE_URL, fail_action))
    else:
        logger.warning(
            'Gather2 Core server and/or token are not set, {}.'.format(fail_action))

    return False  # it's not possible to connect with core


def get_survey_url(survey_id):
    '''
    Returns Gather2 Core url to submit survey responses
    '''
    GATHER_CORE_URL = os.environ.get('GATHER_CORE_URL', '')

    return '{core_url}/surveys/{survey_id}/responses/'.format(
        core_url=GATHER_CORE_URL,
        survey_id=survey_id,
    )
