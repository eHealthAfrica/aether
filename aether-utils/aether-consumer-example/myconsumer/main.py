import contextlib
import errno
import os
import json
import signal

from aether.consumer import KafkaConsumer
from blessings import Terminal
from time import sleep

DEFAULT_TIMEOUT_MESSAGE = os.strerror(errno.ETIME)
KAFKA_HOST = "kafka:29092"


class timeout(contextlib.ContextDecorator):
    def __init__(self, seconds, *, timeout_message=DEFAULT_TIMEOUT_MESSAGE, suppress_timeout_errors=False):
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

t = Terminal()

def bold(obj):
    print(t.bold(obj))

def norm(obj):
    print(t.bold(obj))

def error(obj):
    with t.location(int(t.width/2 - len(obj)/2), 0):
        print(t.black_on_white(obj))

def pjson(obj):
    print(t.bold(json.dumps(obj, indent=2)))

class KafkaViewer(object):

    def __init__(self):
        self.killed = False
        signal.signal(signal.SIGINT, self.kill)
        signal.signal(signal.SIGTERM, self.kill)
        self.start()
        self.topics()

    def ask(self, options):
        bold("Select an option from the list")
        for x, opt in enumerate(options, 1):
            line = "%s ) %s" % (x, opt)
            norm(line)
        while True:
            x = input("choices: ( %s ) : " % ([x+1 for x in range(len(options))]))
            try:
                res = options[int(x)-1]
                return res
            except Exception as err:
                error("%s is not a valid option | %s" % (x, err))

    def start(self):
        while True:
            try:
                with timeout(5):
                    bold("Please attach to this container and press enter to begin | docker attach %s" % os.environ['HOSTNAME'])
                    input("...\n")
                    return
            except TimeoutError:
                if self.killed:
                    return

    def get_consumer(self, quiet=False, topic=None):
        args = {}
        with open("./myconsumer/conf.json") as f:
            args = json.load(f)
        if not quiet:
            t.clear()
            pjson(["Creating Consumer from conf.json args:", args])
        self.consumer = KafkaConsumer(**args)
        if topic:
            self.consumer.subscribe(topic)

    def kill(self, *args, **kwargs):
        self.killed = True

    def topics(self):
        while True:
            t.clear()
            self.get_consumer(quiet=True)
            quit_str = "Exit KafkaViewer"
            topics = [i for i in self.consumer.topics()]
            topics.append(quit_str)
            if not topics:
                bold("No topics available")
                raise IOError("No topics available")
            bold("Choose a Topic to View")
            topic = self.ask(topics)
            if topic is quit_str:
                return
            self.get_consumer(topic=topic)
            self.consumer.seek_to_beginning()
            self.show_topic()

    def show_topic(self):
        messages = self.consumer.poll_and_deserialize(max_records=100)
        if not messages:
            norm("No messages available!")
            return
        pjson(messages)
        part = 0
        choices = [i for i in messages.keys()]
        if len(choices) > 1:
            bold("Choose a Parition to View")
            part = ask(choices)
        messages = messages.get(choices[0])
        pjson(messages)



viewer = KafkaViewer()









