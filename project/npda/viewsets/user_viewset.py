from rest_framework import viewsets
from ..models import NPDAUser
from ..serializers import UserSerializer


# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
    queryset = NPDAUser.objects.all()
    serializer_class = UserSerializer
