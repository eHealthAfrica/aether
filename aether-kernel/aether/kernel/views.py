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

from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from rest_framework import permissions, versioning

SchemaView = get_schema_view(
    openapi.Info(
        title='Aether API',
        default_version='v1',
    ),
    public=True,
    permission_classes=(permissions.AllowAny, ),
)


class AetherSchemaView(SchemaView):

    versioning_class = versioning.URLPathVersioning

    def get(self, *args, **kwargs):
        # this SchemaView doesn't know about realms, so we'll strip that out
        kwargs.pop('realm', None)
        return super().get(*args, **kwargs)
