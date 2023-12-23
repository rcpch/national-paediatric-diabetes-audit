from rest_framework import serializers
import nhs_number
from ..models import Patient
from ..general_functions import validate_postcode


# Serializers define the API representation.
class PatientSerializer(serializers.HyperlinkedModelSerializer):
    def validate(self, data):
        if data["death_date"] < data["date_of_birth"]:
            raise serializers.ValidationError(
                "Date of death cannot be before date of birth."
            )
        if data["death_date"] < data["diagnosis_date"]:
            raise serializers.ValidationError(
                "Date of diagnosis cannot be after date of death."
            )
        if data["diagnosis_date"] < data["date_of_birth"]:
            raise serializers.ValidationError(
                "Date of diagnosis cannot be before date of birth."
            )
        return data

    def validate_nhs_number(self, value):
        if nhs_number.is_valid(str(value).strip(" ")):
            return str(value).strip(" ")
        else:
            raise serializers.ValidationError("Invalid NHS Number")

    def validate_postcode(self, value):
        if validate_postcode(value):
            return value
        raise serializers.ValidationError("Invalid postcode.")

    class Meta:
        model = Patient
        fields = "__all__"
