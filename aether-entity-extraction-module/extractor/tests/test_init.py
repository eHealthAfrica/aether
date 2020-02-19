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

import pytest
from . import *  # noqa

from extractor import main


def test__init_main(redis_fn_scope):
    try:
        container = main()
        assert container.stopped is False
        assert container.is_alive() is True
        assert container.processed_submissions.qsize() == 0
        with pytest.raises(RuntimeError):
            container.start()
    except Exception as unexpected:
        assert False, str(unexpected)
    finally:
        container.stop()
        assert container.stopped is True
        assert container.is_alive() is False
        with pytest.raises(RuntimeError):
            container.stop()
