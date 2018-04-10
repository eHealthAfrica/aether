#!/usr/bin/env python
import os
import sys
from time import sleep

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1].strip() == "test":
            print("starting producer for test")
            from producer import aether_producer
            aether_producer.main_loop(test=True)
            print("Started Producer for Test")
        else:
            print ("invalid argument: %s" % sys.argv[1])
    else:
        print("starting producer")
        print("waiting for requisites")
        from producer import aether_producer
        aether_producer.main_loop()
        print("Started Producer")
