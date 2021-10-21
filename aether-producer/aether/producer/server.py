# Copyright (C) 2021 by eHealth Africa : http://www.eHealthAfrica.org
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

from datetime import datetime
from functools import wraps
import json

from flask import Flask, request, Response

from gevent.pool import Pool
from gevent.pywsgi import WSGIServer

from aether.producer.settings import (
    LOG_LEVEL,
    REVISION,
    SETTINGS,
    VERSION,
    get_logger,
)
from aether.producer.topic import TopicStatus

# Get Auth details from env
_admin_name = SETTINGS.get_required('producer_admin_user')
_admin_password = SETTINGS.get_required('producer_admin_pw')


class ServerMixin():
    # Serves status & healthcheck over HTTP

    app = None
    logger = None

    def serve(self):
        self.app = Flask('AetherProducer')  # pylint: disable=invalid-name
        self.logger = get_logger('Producer', self.app.logger)
        if LOG_LEVEL == 'DEBUG':
            self.app.debug = True

        self.app.config['JSONIFY_PRETTYPRINT_REGULAR'] = SETTINGS \
            .get('flask_settings', {}) \
            .get('pretty_json_status', False)

        server_ip = SETTINGS.get('server_ip', '')
        server_port = int(SETTINGS.get('server_port', 5005))

        pool_size = SETTINGS.get('flask_settings', {}).get('max_connections', 3)
        self.worker_pool = Pool(pool_size)

        # https://www.gevent.org/api/gevent.pywsgi.html#gevent.pywsgi.WSGIServer
        self.http = WSGIServer(
            listener=(server_ip, server_port),
            application=self.app.wsgi_app,
            spawn=self.worker_pool,
            log=None,  # disable request logging
        )
        self.http.start()

        self.add_endpoints()

    def add_endpoints(self):
        # public
        self.register('health', self.request_health)
        self.register('healthcheck', self.request_healthcheck)
        self.register('kernelcheck', self.request_kernelcheck)
        self.register('kafkacheck', self.request_kafkacheck)
        self.register('check-app', self.request_check_app)
        self.register('check-app/aether-kernel', self.request_kernelcheck)
        self.register('check-app/kafka', self.request_kafkacheck)

        # protected
        self.register('status', self.request_status)
        self.register('topics', self.request_topics)
        self.register('pause', self.request_pause)
        self.register('resume', self.request_resume)
        self.register('rebuild', self.request_rebuild)

    def register(self, route_name, fn):
        self.app.add_url_rule(f'/{route_name}', route_name, view_func=fn)

    def return_json(self, data, status=None):
        return Response(
            response=json.dumps(data),
            status=status,
            mimetype='application/json',
            content_type='application/json',
        )

    # Basic Auth implementation

    def check_auth(self, username, password):
        return username == _admin_name and password == _admin_password

    def request_authentication(self):
        with self.app.app_context():
            return Response('Bad Credentials', 401,
                            {'WWW-Authenticate': 'Basic realm="Login Required"'})

    def requires_auth(f):
        @wraps(f)
        def decorated(self, *args, **kwargs):
            auth = request.authorization
            if not auth or not self.check_auth(auth.username, auth.password):
                return self.request_authentication()
            return f(self, *args, **kwargs)
        return decorated

    # Exposed Request Endpoints

    def request_health(self):
        with self.app.app_context():
            return self.return_json({'healthy': True})

    def request_healthcheck(self):
        with self.app.app_context():
            try:
                expired = self.check_thread_health()
                if not expired:
                    return self.return_json({'healthy': True})
                else:
                    return self.return_json(expired, 500)

            except Exception as err:
                self.app.logger.error(f'Unexpected error: {err}')
                return Response(f'Unexpected error: {err}', 500)

    def request_kernelcheck(self):
        with self.app.app_context():
            healthy = self.check_kernel()
            return self.return_json(
                {'healthy': healthy},
                status=200 if healthy else 424,  # Failed dependency
            )

    def request_kafkacheck(self):
        with self.app.app_context():
            healthy = self.kafka_available()
            return self.return_json(
                {'healthy': healthy},
                status=200 if healthy else 424,  # Failed dependency
            )

    def request_check_app(self):
        with self.app.app_context():
            return self.return_json({
                'app_name': 'aether-producer',
                'app_version': VERSION,
                'app_revision': REVISION,
                'now': datetime.now().isoformat(),
            })

    @requires_auth
    def request_status(self):
        with self.app.app_context():
            return self.return_json(self.check_status())

    @requires_auth
    def request_topics(self):
        with self.app.app_context():
            return self.return_json(self.check_topics())

    # Topic Command API

    @requires_auth
    def request_pause(self):
        return self.handle_topic_command(request, TopicStatus.PAUSED)

    @requires_auth
    def request_resume(self):
        return self.handle_topic_command(request, TopicStatus.NORMAL)

    @requires_auth
    def request_rebuild(self):
        return self.handle_topic_command(request, TopicStatus.REBUILDING)

    @requires_auth
    def handle_topic_command(self, request, status):
        with self.app.app_context():
            realm = request.args.get('realm')
            if not realm:
                return Response('A realm must be specified', 422)

            topic = request.args.get('topic')
            if not topic:
                return Response('A topic must be specified', 422)

            manager = self.get_manager(realm)
            if not manager:
                return Response(f'Bad realm name: {realm}', 422)

            schema_wrapper = manager.schemas.get(topic)
            if not schema_wrapper:
                return Response(f'Realm {realm} has no topic {topic}', 422)

            if status is TopicStatus.PAUSED:
                fn = manager.pause
            if status is TopicStatus.NORMAL:
                fn = manager.resume
            if status is TopicStatus.REBUILDING:
                fn = manager.rebuild

            try:
                res = fn(schema_wrapper)
                if not res:
                    return Response(f'Operation failed on {topic}', 500)

                return Response(f'Success for status {status} on {topic}', 200)
            except Exception as err:
                return Response(f'Operation failed on {topic} with: {err}', 500)

    def check_thread_health(self):
        raise NotImplementedError

    def check_kernel(self):
        raise NotImplementedError

    def kafka_available(self):
        raise NotImplementedError

    def get_manager(self, realm):
        raise NotImplementedError
