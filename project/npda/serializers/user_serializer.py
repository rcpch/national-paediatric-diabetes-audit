from rest_framework import serializers
from django.apps import apps

NPDAUser = apps.get_model("npda", "NPDAUser")


# Serializers define the API representation.
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = NPDAUser
        fields = "__all__"
