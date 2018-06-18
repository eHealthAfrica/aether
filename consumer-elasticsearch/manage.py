#!/usr/bin/env python
import os
import sys
from time import sleep

if __name__ == '__main__':
    print("starting ElasticSearch Consumer")
    print("waiting for requisites")
    from consumer import elasticsearch_consumer
    elasticsearch_consumer.main_loop()
    print("Started ElasticSearch Consumer")
