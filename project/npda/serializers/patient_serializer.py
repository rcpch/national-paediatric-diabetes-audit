from rest_framework import serializers
from ..models import Patient

# Serializers define the API representation.
class PatientSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Patient
        fields = "__all__"
