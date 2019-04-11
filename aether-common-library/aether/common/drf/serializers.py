# -*- coding: utf-8 -*-

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

import urllib

from django.conf import settings
from django.urls import resolve

from rest_framework import serializers
from rest_framework.reverse import reverse


def custom_reverse(viewname, args=None, kwargs=None, request=None, format=None, **extra):
    if not kwargs:
        kwargs = {}

    if settings.GATEWAY_HOST:
        path_kwargs = resolve(request.path).kwargs
        kwargs['realm'] = path_kwargs['realm']

    return reverse(viewname=viewname, args=args, kwargs=kwargs, request=request, format=format, **extra)


class HyperlinkedRelatedField(serializers.HyperlinkedRelatedField):

    def __init__(self, view_name=None, **kwargs):
        super(HyperlinkedRelatedField, self).__init__(view_name, **kwargs)

        # override the reverse method used internally
        self.reverse = custom_reverse


class HyperlinkedIdentityField(serializers.HyperlinkedIdentityField, HyperlinkedRelatedField):
    pass


class FilteredHyperlinkedRelatedField(HyperlinkedRelatedField):
    '''
    This custom field does essentially the same thing as
    ``serializers.HyperlinkedRelatedField``.

    The only difference is that the url of a foreign key relationship will be:

        {
            ...
            'children_url': '/children?parent=<parent-id>'
            ...
        }

    Instead of:

        {
            ...
            'children_url': '/parent/<parent-id>/children/'
            ...
        }

    '''

    def get_url(self, obj, view_name, request, format):
        lookup_field_value = obj.instance.pk
        result = '{}?{}'.format(
            self.reverse(view_name, kwargs={}, request=request, format=format),
            urllib.parse.urlencode({self.lookup_field: lookup_field_value})
        )
        return result
