import sys
import unittest
from time import sleep


def run():
    sleep(5)
    loader = unittest.TestLoader()
    suite = loader.discover(".", pattern="test_*.py")
    result = not unittest.TextTestRunner(verbosity=1).run(suite).wasSuccessful()
    sys.exit(result)


if __name__ == "__main__":
    run()
