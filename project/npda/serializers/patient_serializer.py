from rest_framework import serializers
import nhs_number
from ..models import Patient


# Serializers define the API representation.
class PatientSerializer(serializers.HyperlinkedModelSerializer):
    def validate_nhs_number(self, value):
        if nhs_number.is_valid(str(value)):
            return value
        else:
            raise serializers.ValidationError("Invalid NHS Number")

    def validate_death_date(self, value):
        if value and self.date_of_birth > value:
            raise serializers.ValidationError(
                "Date of death cannot be before date of birth."
            )
        return value

    class Meta:
        model = Patient
        fields = "__all__"
