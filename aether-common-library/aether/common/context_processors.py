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


from django.conf import settings

from .multitenancy.utils import get_current_realm


def aether_context(request):
    context = {
        'dev_mode': settings.DEBUG,
        'app_id': settings.APP_ID,
        'app_name': settings.APP_NAME,
        'app_link': settings.APP_LINK,
        'app_version': settings.VERSION,
        'app_revision': settings.REVISION,
    }

    if settings.KEYCLOAK_URL:
        realm = get_current_realm(request)
        redirect = request.build_absolute_uri().replace(request.get_full_path(), '/') + settings.URL_ID
        url = f'{settings.BASE_HOST}/auth/user/{realm}/refresh?redirect={redirect}'

        context['jwt_login'] = url

    return context
