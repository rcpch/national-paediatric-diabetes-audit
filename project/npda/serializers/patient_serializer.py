from rest_framework import serializers
import nhs_number
from django.apps import apps
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from ..general_functions import validate_postcode

Patient = apps.get_model("npda", "Patient")
Organisation = apps.get_model("npda", "Organisation")

from ..general_functions import gp_practice_for_postcode


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "/patient/1/",
            value={
                "": "",
                "": "",
                "": "",
                "": "",
                "": "",
                "": "",
                "": "",
                "": "",
                "": "",
                "": "",
            },
            response_only=True,
        )
    ]
)
class PatientSerializer(serializers.HyperlinkedModelSerializer):
    def validate(self, data):
        if data["death_date"] is not None:
            if data["death_date"] < data["date_of_birth"]:
                raise serializers.ValidationError(
                    "Date of death cannot be before date of birth."
                )
            if data["death_date"] < data["diagnosis_date"]:
                raise serializers.ValidationError(
                    "Date of diagnosis cannot be after date of death."
                )
        if data["diagnosis_date"] is not None:
            if data["diagnosis_date"] < data["date_of_birth"]:
                raise serializers.ValidationError(
                    "Date of diagnosis cannot be before date of birth."
                )
        if (
            data["gp_practice_ods_code"] is None
            and data["gp_practice_postcode"] is None
        ):
            raise serializers.ValidationError(
                "Either GP Practice postcode or ODS code must be supplied."
            )

        if data["gp_practice_postcode"] is not None:
            try:
                gp_practice_for_postcode(data["gp_practice_postcode"])
            except Exception as error:
                raise serializers.ValidationError(error)

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
        fields = (
            "nhs_number",
            "sex",
            "date_of_birth",
            "postcode",
            "ethnicity",
            "index_of_multiple_deprivation_quintile",
            "diabetes_type",
            "diagnosis_date",
            "death_date",
            "gp_practice_ods_code",
            "gp_practice_postcode",
        )
