# python imports
from datetime import date

# django imports
from django.apps import apps
from django.core.exceptions import ValidationError
from django import forms

# third-party imports
from dateutil.relativedelta import relativedelta

# project imports
import nhs_number
from ..models import Patient
from ...constants.styles.form_styles import *
from ..general_functions import (
    validate_postcode,
    gp_practice_for_postcode,
)
from ..validators import not_in_the_future_validator


class DateInput(forms.DateInput):
    input_type = "date"


class NHSNumberField(forms.CharField):
    def to_python(self, value):
        number = super().to_python(value)
        normalised = nhs_number.normalise_number(number)

        # For some combinations we get back an empty string (eg '719-573 0220')
        return normalised or value

    def validate(self, value):
        if value and not nhs_number.is_valid(value):
            raise ValidationError("Invalid NHS number")


class PostcodeField(forms.CharField):
    def to_python(self, value):
        postcode = super().to_python(value)

        if postcode:
            return postcode.upper().replace(" ", "").replace("-", "")

class PatientForm(forms.ModelForm):

    class Meta:
        model = Patient
        fields = [
            "nhs_number",
            "sex",
            "date_of_birth",
            "postcode",
            "ethnicity",
            "diabetes_type",
            "diagnosis_date",
            "death_date",
            "gp_practice_ods_code",
            "gp_practice_postcode",
        ]
        field_classes = {
            "nhs_number": NHSNumberField,
            "postcode": PostcodeField,
            "gp_practice_postcode": PostcodeField
        }
        widgets = {
            "nhs_number": forms.TextInput(
                attrs={"class": TEXT_INPUT},
            ),
            "sex": forms.Select(),
            "date_of_birth": DateInput(),
            "postcode": forms.TextInput(attrs={"class": TEXT_INPUT}),
            "ethnicity": forms.Select(),
            "diabetes_type": forms.Select(),
            "diagnosis_date": DateInput(),
            "death_date": DateInput(),
            "gp_practice_ods_code": forms.TextInput(attrs={"class": TEXT_INPUT}),
            "gp_practice_postcode": forms.TextInput(attrs={"class": TEXT_INPUT}),
        }

    def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data["date_of_birth"]

        if date_of_birth:
            today = date.today()
            age = relativedelta(today, date_of_birth).years

            not_in_the_future_validator(date_of_birth)

            if age >= 25:
                raise ValidationError(
                    "NPDA patients cannot be 25+ years old. This patient is %(age)s",
                    params={"age": age}
                )

        return date_of_birth

    def clean_diagnosis_date(self):
        diagnosis_date = self.cleaned_data["diagnosis_date"]
        not_in_the_future_validator(diagnosis_date)

        return diagnosis_date

    def clean_death_date(self):
        death_date = self.cleaned_data["death_date"]
        not_in_the_future_validator(death_date)

        return death_date

    def clean(self):
        cleaned_data = super().clean()
        date_of_birth = cleaned_data.get("date_of_birth")
        diagnosis_date = cleaned_data.get("diagnosis_date")
        death_date = cleaned_data.get("death_date")
        gp_practice_ods_code = cleaned_data.get("gp_practice_ods_code")
        gp_practice_postcode = cleaned_data.get("gp_practice_postcode")

        if diagnosis_date is not None and date_of_birth is not None:
            if diagnosis_date < date_of_birth:
                self.add_error(
                    "diagnosis_date",
                    ValidationError(
                        "'Date of Diabetes Diagnosis' cannot be before 'Date of Birth'"
                    ),
                )

        if death_date is not None and date_of_birth is not None:
            if death_date < date_of_birth:
                self.add_error(
                    "death_date",
                    ValidationError("'Death Date' cannot be before 'Date of Birth'"),
                )

        if death_date is not None and diagnosis_date is not None:
            if death_date < diagnosis_date:
                self.add_error(
                    "death_date",
                    ValidationError(
                        "'Death Date' cannot be before 'Date of Diabetes Diagnosis'"
                    ),
                )

        if gp_practice_ods_code is None and gp_practice_postcode is None:
            raise ValidationError(
                {
                    "gp_practice_ods_code": [
                        "'GP Practice ODS code' and 'GP Practice postcode' cannot both be empty"
                    ]
                }
            )

        if not gp_practice_ods_code and gp_practice_postcode:
            try:
                ods_code = gp_practice_for_postcode(gp_practice_postcode)

                if not ods_code:
                    raise ValidationError(
                        "Could not find GP practice with that postcode"
                    )
                else:
                    cleaned_data["gp_practice_ods_code"] = ods_code
            except Exception as error:
                raise ValidationError({"gp_practice_postcode": [error]})

        return cleaned_data
