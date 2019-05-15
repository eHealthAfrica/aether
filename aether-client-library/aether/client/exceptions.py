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


# An Exception Class to wrap all handled API exceptions
class AetherAPIException(Exception):
    def __init__(self, *args, **kwargs):
        msg = {k: v for k, v in kwargs.items()}
        for k, v in kwargs.items():
            setattr(self, k, v)
        super(AetherAPIException, self).__init__(msg)
