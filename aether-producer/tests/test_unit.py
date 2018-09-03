#!/usr/bin/env python

# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
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

from . import *

@pytest.mark.unit
def test_kernel_handler_expected_exception():
    kernel_value = 1
    obj = ObjectWithKernel(kernel_value)
    with KernelHandler(obj, [AttributeError]):
        new_variable = obj.missing
    assert(obj.kernel == kernel_value)

@pytest.mark.unit
def test_kernel_handler_unexpected_exception():
    kernel_value = 1
    obj = ObjectWithKernel(kernel_value)
    try:
        with KernelHandler(obj):
            new_variable = obj.missing
            assert(False), "Error should have been thrown"
    except AttributeError:
        pass
    else:
        assert(False), "Should have thrown an AttributeError"
    assert(obj.kernel == None)
