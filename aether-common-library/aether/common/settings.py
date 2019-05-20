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

import os

from django_eha_sdk.conf.settings import *  # noqa
from django_eha_sdk.conf.settings import INSTALLED_APPS


# Common Configuration
# ------------------------------------------------------------------------------

APP_NAME = os.environ.get('APP_NAME', 'aether')
APP_LINK = os.environ.get('APP_LINK', 'http://aether.ehealthafrica.org')

APP_NAME_HTML = '<b>ae</b>ther'
APP_FAVICON = 'aether/images/aether.png'
APP_LOGO = 'aether/images/aether-white.png'

APP_EXTRA_STYLE = 'aether/css/styles.css'
APP_EXTRA_META = (
    'A free, open source development platform'
    ' for data curation, exchange, and publication'
)

INSTALLED_APPS += ['aether.common', ]  # includes static content
