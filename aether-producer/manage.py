#!/usr/bin/env python

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

import os
import sys
from time import sleep

if __name__ == '__main__':

    if len(sys.argv) > 1:
        if sys.argv[1].strip() == "test":
            print("starting producer for test")
            from producer import aether_producer
            aether_producer.main(test=True)
            print("Started Producer for Test")
        else:
            print ("invalid argument: %s" % sys.argv[1])
    else:
        print("starting producer")
        print("waiting for requisites")
        from producer import aether_producer
        aether_producer.main(test=False)
        print("Started Producer")
