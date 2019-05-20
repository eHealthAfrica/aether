#!/usr/bin/env python

# Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
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

# From : https://gist.github.com/TySkby/143190ad1b88c6115597c45f996b030c#file-timeout-py-L11

import contextlib
import errno
import os
import signal


DEFAULT_TIMEOUT_MESSAGE = os.strerror(errno.ETIME)


class timeout(contextlib.ContextDecorator):
    def __init__(
            self,
            seconds,
            *,
            timeout_message=DEFAULT_TIMEOUT_MESSAGE,
            suppress_timeout_errors=False):
        self.seconds = int(seconds)
        self.timeout_message = timeout_message
        self.suppress = bool(suppress_timeout_errors)

    def _timeout_handler(self, signum, frame):
        raise TimeoutError(self.timeout_message)

    def __enter__(self):
        signal.signal(signal.SIGALRM, self._timeout_handler)
        signal.alarm(self.seconds)

    def __exit__(self, exc_type, exc_val, exc_tb):
        signal.alarm(0)
        if self.suppress and exc_type is TimeoutError:
            return True
