from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group


SURVEYOR_GROUP_NAME = 'surveyor'


def get_surveyor_group():
    surveyor_group, _ = Group.objects.get_or_create(name=SURVEYOR_GROUP_NAME)
    return surveyor_group


def get_surveyors():
    '''
    Extracts the list of valid surveyors from the users list.

    Conditions:
    - active users
    - have the group `surveyor`

    '''

    surveyors = get_user_model().objects \
                                .filter(is_active=True) \
                                .order_by('username')

    # skipping annoying error that only happens with an empty database in the bootstrap step
    #
    # `django.db.utils.ProgrammingError: relation "auth_group" does not exist`
    #
    #   File "/code/aether/odk/api/admin.py", line 12, in <module>
    #     class XFormForm(forms.ModelForm):
    #   File "/code/aether/odk/api/admin.py", line 18, in XFormForm
    #     queryset=get_surveyors(),
    #
    try:
        # make sure that the group exists
        surveyor_group = get_surveyor_group()
        return surveyors.filter(groups__name=surveyor_group.name)
    except Exception:  # pragma: no cover
        return surveyors


def flag_as_surveyor(user):
    '''
    Adds the group "surveyor" to the user.
    '''

    user.groups.add(get_surveyor_group())
    user.save()
