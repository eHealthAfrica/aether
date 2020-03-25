# Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
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

import json
import logging
import os


class Settings(dict):
    # A container for our settings

    def __init__(self, file_path=None):
        self.load(file_path)

    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def get_required(self, key):
        return self.__getitem__(key)

    def __getitem__(self, key):
        result = os.environ.get(key.upper())
        if result is None:
            result = super().__getitem__(key.lower())

        return result

    def load(self, path):
        with open(path) as f:
            obj = json.load(f)
            for k in obj:
                self[k.lower()] = obj.get(k)


def get_logger(name, logger=None):
    if not logger:
        logger = logging.getLogger(name)
        logger.propagate = False

    try:
        handler = logger.handlers[0]
    except IndexError:
        handler = logging.StreamHandler()
        logger.addHandler(handler)

    handler.setFormatter(logging.Formatter(f'%(asctime)s [{name}] %(levelname)-8s %(message)s'))

    logger.setLevel(LOG_LEVEL)

    return logger


def _get_kafka_settings():
    kafka_settings = {}
    kafka_settings['bootstrap.servers'] = SETTINGS.get_required('kafka_url')

    mode = SETTINGS.get('kafka_security', '')
    if mode.lower() == 'sasl_plaintext':
        # Let Producer use Kafka SU to produce
        kafka_settings['security.protocol'] = 'SASL_PLAINTEXT'
        kafka_settings['sasl.mechanisms'] = 'SCRAM-SHA-256'
        kafka_settings['sasl.username'] = SETTINGS.get_required('kafka_su_user')
        kafka_settings['sasl.password'] = SETTINGS.get_required('kafka_su_pw')

    elif mode.lower() == 'sasl_ssl':
        kafka_settings['security.protocol'] = 'SASL_SSL'
        kafka_settings['sasl.mechanisms'] = 'PLAIN'
        kafka_settings['sasl.username'] = SETTINGS.get_required('kafka_su_user')
        kafka_settings['sasl.password'] = SETTINGS.get_required('kafka_su_pw')

    return kafka_settings


##################################################
# Get settings from config file

here = os.path.dirname(os.path.realpath(__file__))
_default_file_path = os.path.join(here, 'settings.json')

_file_path = os.environ.get('PRODUCER_SETTINGS_FILE', _default_file_path)
SETTINGS = Settings(_file_path)
KAFKA_SETTINGS = _get_kafka_settings()
LOG_LEVEL = logging.getLevelName(SETTINGS.get('log_level', 'INFO'))
