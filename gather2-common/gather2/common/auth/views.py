from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import (
    api_view,
    permission_classes,
    renderer_classes,
)
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response


@api_view(['POST'])
@renderer_classes([JSONRenderer])
@permission_classes([IsAuthenticated, IsAdminUser])
def obtain_auth_token(request):
    '''
    Given a username generates an auth token for him/her.
    If the username does not belong to an existing user,
    it's going to be created with a long and random password.
    '''

    UserModel = get_user_model()
    user_model = UserModel.objects

    try:
        username = request.POST['username']

        # gets the existing user or creates a new one
        try:
            user = user_model.get(username=username)
        except UserModel.DoesNotExist:
            user = user_model.create_user(
                username=username,
                password=user_model.make_random_password(length=100),
            )

        # gets the user token
        token, _ = Token.objects.get_or_create(user=user)

        return Response({'token': token.key})

    except Exception as e:
        return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
