#!/usr/bin/env python
import os
import sys
from time import sleep

if __name__ == '__main__':
    print("starting producer")
    print("waiting for requisites")
    from producer import aether_producer
    aether_producer.main_loop()
    print("Started Producer")
