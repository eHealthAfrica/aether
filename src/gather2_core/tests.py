import pytest

from .models import Survey


@pytest.mark.django_db
def test_my_user():
    a = Survey(name="Hello World")
    assert str(a) == "None - Hello World"
