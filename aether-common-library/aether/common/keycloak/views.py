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
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.views import LoginView

from django.utils.translation import ugettext as _

from .forms import RealmForm, RealmAuthenticationForm
from .utils import post_authenticate, get_realm_auth_url


class KeycloakLoginView(LoginView):
    '''
    Executes Login process in three steps:

    1.- Displays the realm form. (GET)

    2.- Checks the realm and redirects to keycloak server to continue login. (POST)

    3.- Receives keycloak response and finalize authentication process. (GET)
    '''

    template_name = settings.DEFAULT_KEYCLOAK_TEMPLATE

    def __init__(self, *args, **kwargs):
        if settings.GO_TO_KEYCLOAK:
            self.authentication_form = RealmForm
        else:
            self.authentication_form = RealmAuthenticationForm

        super(KeycloakLoginView, self).__init__(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        if settings.GO_TO_KEYCLOAK:
            try:
                user = post_authenticate(request)
                if user:
                    auth_login(request, user)
                    return HttpResponseRedirect(self.get_success_url())
            except Exception:
                messages.error(request, _('An error ocurred while authenticating against keycloak'))

        return super(KeycloakLoginView, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        if settings.GO_TO_KEYCLOAK:
            # save the current realm in the session
            self.request.session[settings.REALM_COOKIE] = form.cleaned_data.get('realm')
            return HttpResponseRedirect(get_realm_auth_url(self.request))

        return super(KeycloakLoginView, self).form_valid(form)
