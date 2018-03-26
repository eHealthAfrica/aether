import pytest
from . import py2


@pytest.fixture(scope='module')
def info():
    return "hi"


@py2
def test_1(info):
    assert info is not None
