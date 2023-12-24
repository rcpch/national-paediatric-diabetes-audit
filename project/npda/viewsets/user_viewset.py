from rest_framework import viewsets
from ..serializers import UserSerializer, OrganisationSerializer
from django.apps import apps

NPDAUser = apps.get_model("npda", "NPDAUser")


# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
    queryset = NPDAUser.objects.all()
    serializer_class = UserSerializer
