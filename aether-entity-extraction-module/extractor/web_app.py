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

import logging
import json
from flask import Flask, Response
from gevent.pool import Pool
from gevent.pywsgi import WSGIServer
from . import settings

logger = logging.getLogger(__name__)
logger.setLevel(settings.LOGGING_LEVEL)


class WebApp():

    def __init__(self):
        # Start endpoints
        self.app = Flask(__name__)  # pylint: disable=invalid-name
        self.add_endpoints()
        self.serve()

    def add_endpoints(self):
        # URLS configured here
        self.register('healthcheck', self.request_healthcheck)

    def register(self, route_name, fn):
        self.app.add_url_rule('/%s' % route_name, route_name, view_func=fn)

    def serve(self):
        if settings.LOGGING_LEVEL == 'DEBUG':
            self.app.debug = True
        self.app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
        self.http = WSGIServer(
            (settings.HOST, settings.WEB_SERVER_PORT),
            self.app,
            spawn=Pool(3)
        )
        self.http.serve_forever()

    # Exposed Request Endpoints

    def request_healthcheck(self):
        with self.app.app_context():
            return Response(json.dumps({'healthy': True}))
