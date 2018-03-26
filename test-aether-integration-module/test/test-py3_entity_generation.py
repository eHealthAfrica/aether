import pytest
from . import py3


@pytest.fixture(scope='module')
def info():
    return "hi"


@py3
def test_1(info):
    assert info is not None


def test_2(info):
    assert info is not None
