from rest_framework import serializers
from django.apps import apps

Organisation = apps.get_model("npda", "Organisation")


class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = "__all__"
