from rest_framework import serializers
from ..models import NPDAUser


# Serializers define the API representation.
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = NPDAUser
        fields = "__all__"
