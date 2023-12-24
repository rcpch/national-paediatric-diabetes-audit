from rest_framework import serializers
from django.apps import apps
from ..serializers import OrganisationSerializer

NPDAUser = apps.get_model("npda", "NPDAUser")


# Serializers define the API representation.
class UserSerializer(serializers.ModelSerializer):
    organisation_employer = OrganisationSerializer(many=False, read_only=True)

    class Meta:
        model = NPDAUser
        fields = "__all__"
