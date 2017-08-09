import json
import os
import requests

from sync.settings import logger


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
        return {
            'Authorization': 'Token {token}'.format(token=token),
            'Content-Type': 'application/json',
        }
    return None


def test_connection():
    '''
    Checks possible connection with GATHER2 CORE
    '''

    url = get_core_server_url()
    token = os.environ.get('GATHER_CORE_TOKEN', '')
    err_msg = 'syncing data to core will not work'

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
    Returns Gather2 Core url to submit surveys
    '''
    return '{core_url}/surveys/{survey_id}'.format(
        core_url=get_core_server_url(),
        survey_id=survey_id
    )


def get_survey_responses_url(survey_id, response_id=None):
    '''
    Returns Gather2 Core url to submit survey responses
    '''
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
    resp = requests.get(url, headers=get_auth_header())
    resp.raise_for_status()
    data = resp.json()

    results = data['results']
    while data['next']:
        resp = requests.get(data['next'], headers=get_auth_header())
        resp.raise_for_status()
        data = resp.json()
        results += data['results']

    return results


def submit_to_core(response, survey_id, response_id=None):
    if survey_id is None:
        raise Exception('Cannot submit response without survey!')

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
