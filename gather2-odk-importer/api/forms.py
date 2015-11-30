from django import forms


class XFormCreateForm(forms.Form):

    """
    form for capturing XForm data

    This is not a model form as we want to take an xml file and then save it
    into a text field in the database
    """

    xml_file = forms.FileField()

    # This is a hidden input because we want to populate it from the URL they
    # hit
    username = forms.CharField(
        widget=forms.HiddenInput(),
        max_length=100
    )

    title = forms.CharField(
        max_length=100
    )

    description = forms.CharField(
        widget=forms.Textarea()
    )
