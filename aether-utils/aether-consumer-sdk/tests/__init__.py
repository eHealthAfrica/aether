import pytest
import sys
from time import sleep


@pytest.fixture(scope="session")
def one():
    return 1
