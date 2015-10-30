import pytest

from .models import FormTemplate


@pytest.mark.django_db
def test_formtemplate():
    a = FormTemplate(id=12, name="A name")
    assert str(a) == "12 - A name"
