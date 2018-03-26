import pytest
# from . import aether_client


@pytest.fixture(scope='module')
def info():
    return "hi"


def test_1(info):
    assert info is not None
