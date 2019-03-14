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

from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .utils import filter_by_realm, is_accessible_by_realm


class MtViewSetMixin(object):
    '''
    Defines ``get_queryset`` method to include filter by realm.

    Expects ``mt_field`` property.

    Adds two new methods:
        - ``get_object_or_404(pk)`` raises NO_FOUND error if the instance
          does not exists or is not accessible by current realm.
        - ``get_object_or_403(pk)`` raises FORBIDDEN error if the instance
          exists and is not accessible by current realm.

    Adds a detail endpoint ``/is-accessible`` only permitted with HEAD method,
    returns the following statuses:
        - 403 FORBIDDEN   if the instance is not accessible by current realm
        - 404 NOT_FOUND   if the instance does not exist
        - 204 NO_CONTENT  otherwise
    '''

    mt_field = None

    def get_queryset(self):
        '''
        Overrides ``get_queryset`` method to include filter by realm in each query
        '''

        qs = super(MtViewSetMixin, self).get_queryset()
        return filter_by_realm(self.request, qs, self.mt_field)

    def get_object_or_404(self, pk):
        '''
        Custom method that raises NO_FOUND error
        if the instance does not exists or is not accessible by current realm
        otherwise return the instance
        '''

        return get_object_or_404(self.get_queryset(), pk=pk)

    def get_object_or_403(self, pk):
        '''
        Custom method that raises FORBIDDEN error
        if the instance exists and is not accessible by current realm
        otherwise returns the instance or ``None`` if it does not exist
        '''

        # without filtering by realm
        qs = super(MtViewSetMixin, self).get_queryset()
        if not qs.filter(pk=pk).exists():
            return None

        obj = qs.get(pk=pk)
        if not is_accessible_by_realm(self.request, obj):
            raise PermissionDenied(_('Not accessible by this realm'))

        return obj

    @action(detail=True, methods=['head'], url_path='is-accessible')
    def is_accessible(self, request, pk=None):
        '''
        Returns the following statuses:
            - 404 NOT_FOUND   if the instance does not exist
            - 403 FORBIDDEN   if the instance is not accessible by current realm
            - 204 NO_CONTENT  otherwise
        '''

        self.get_object_or_403(pk)
        self.get_object_or_404(pk)

        return Response(status=204)
