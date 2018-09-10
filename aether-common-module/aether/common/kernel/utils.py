# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import os
import requests

from django.utils.translation import ugettext as _

from . import errors
from ..conf.settings import logger


def get_kernel_server_url():
    if bool(os.environ.get('TESTING')):
        return os.environ.get('AETHER_KERNEL_URL_TEST')
    else:
        return os.environ.get('AETHER_KERNEL_URL')


def get_kernel_server_token():
    return os.environ.get('AETHER_KERNEL_TOKEN')


def get_auth_header():
    '''
    Returns the Authorization Header if connection to Aether Kernel is possible
    '''

    if test_connection():
        return {'Authorization': f'Token {get_kernel_server_token()}'}
    return None


def test_connection():
    '''
    Checks possible connection with Aether Kernel
    '''

    url = get_kernel_server_url()
    token = get_kernel_server_token()

    if url and token:
        try:
            # check that the server is up
            h = requests.head(url)
            assert h.status_code == 403  # expected response 403 Forbidden
            logger.info(_('Aether Kernel server ({}) is up and responding!').format(url))

            try:
                # check that the token is valid
                g = requests.get(url, headers={'Authorization': f'Token {token}'})
                assert g.status_code == 200, g.content
                logger.info('Aether Kernel token is valid!')

                return True  # it's possible to connect with kernel :D

            except Exception:
                logger.warning(
                    _('Aether Kernel token is not valid for Aether Kernel server ({}).')
                    .format(url))
        except Exception:
            logger.warning(
                _('Aether Kernel server ({}) is not available.')
                .format(url))
    else:
        logger.warning(_('Aether Kernel server and/or token are not set.'))

    return False  # it's not possible to connect with kernel :(


def check_connection():
    '''
    Check if the connection with Kernel server is possible
    '''

    if not test_connection():
        return _('Always Look on the Bright Side of Life!!!')
    return _('Brought to you by eHealth Africa - good tech for hard places')


def get_mappings_url(mapping_id=''):
    '''
    Returns Aether Kernel url for the given mapping
    '''
    return __get_type_url('mappings', mapping_id)


def get_submissions_url(submission_id=None):
    '''
    Returns Aether Kernel url for submissions
    '''
    return __get_type_url('submissions', submission_id)


def get_attachments_url(attachment_id=None):
    '''
    Returns Aether Kernel url for submission attachments
    '''
    return __get_type_url('attachments', attachment_id)


def __get_type_url(model_type, id=None):
    '''
    Returns Aether Kernel url for type "XXX"
    '''
    if not id:
        return '{kernel_url}/{type}/'.format(
            kernel_url=get_kernel_server_url(),
            type=model_type,
        )
    else:
        return '{kernel_url}/{type}/{id}/'.format(
            kernel_url=get_kernel_server_url(),
            type=model_type,
            id=id,
        )


def get_all_docs(url):
    '''
    Returns all documents linked to an url, even with pagination
    '''
    def get_data(url):
        resp = requests.get(url, headers=get_auth_header())
        resp.raise_for_status()
        return resp.json()

    data = {'next': url}
    results = []
    while data.get('next'):
        data = get_data(data['next'])
        results += data['results']

    return results


def submit_to_kernel(submission, mapping_id, submission_id=None):
    '''
    Make the submission to Aether Kernel mapping
    '''
    if mapping_id is None:
        raise errors.SubmissionError(_('Cannot make submission without mapping!'))

    if submission is None:
        raise errors.SubmissionError(_('Cannot make submission without content!'))

    if submission_id:
        # update existing doc
        method = requests.put
        url = get_submissions_url(submission_id)
    else:
        # create new doc
        method = requests.post
        url = get_submissions_url()

    logger.debug('{method} to {url}'.format(method=method, url=url))
    return method(
        url,
        json={
            'payload': submission,
            'mapping': mapping_id,
        },
        headers=get_auth_header(),
    )
