from . import *
from aether.consumer import KafkaConsumer

def test_first():
    assert(one() == 1), "One Should be One"
