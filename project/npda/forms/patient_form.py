# python imports
from datetime import date

# django imports
from django.apps import apps
from django.core.exceptions import ValidationError
from django import forms

# project imports
import nhs_number
from ..models import Patient
from ...constants.styles.form_styles import *
from ..general_functions import (
    validate_postcode,
    gp_practice_for_postcode,
    retrieve_quarter_for_date,
)


class DateInput(forms.DateInput):
    input_type = "date"


class NHSNumberField(forms.CharField):
    def to_python(self, value):
        number = super().to_python(value)
        normalised = nhs_number.normalise_number(number)

        # For some combinations we get back an empty string (eg '719-573 0220')
        return normalised or value

    def validate(self, value):
        if not nhs_number.is_valid(value):
            raise ValidationError("Invalid NHS number")


class PatientForm(forms.ModelForm):

    quarter = forms.ChoiceField(
        choices=[
            (1, 1),
            (2, 2),
            (3, 3),
            (4, 4),
        ],  # Initially empty, will be populated dynamically
        required=True,
        widget=forms.Select(attrs={"class": SELECT}),
        label="Audit Year Quarter",
    )

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
            "quarter",
        ]
        field_classes = {"nhs_number": NHSNumberField}
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
            "quarter": forms.Select(),
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # this is a bound form, so we need to get the quarter from the submission related to the instance
            Submission = apps.get_model("npda", "Submission")
            self.initial["quarter"] = Submission.objects.get(
                patients=self.instance
            ).quarter
        else:
            # this is an unbound form, so we need to set the quarter to current quarter
            self.initial["quarter"] = retrieve_quarter_for_date(
                date_instance=date.today()
            )

    def clean_postcode(self):
        if not self.cleaned_data["postcode"]:
            raise ValidationError("This field is required")

        postcode = (
            self.cleaned_data["postcode"].upper().replace(" ", "").replace("-", "")
        )
        if not validate_postcode(postcode=postcode):
            raise ValidationError("Postcode invalid")
        return postcode

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
            self.add_error(
                "gp_practice_ods_code",
                ValidationError(
                    "GP Practice ODS code and GP Practice postcode cannot both be empty. At least one must be supplied."
                ),
            )

        if not gp_practice_ods_code and gp_practice_postcode:
            try:
                ods_code = gp_practice_for_postcode(gp_practice_postcode)

                if not ods_code:
                    self.add_error(
                        "gp_practice_postcode",
                        ValidationError(
                            "Could not find GP practice with that postcode"
                        ),
                    )
                else:
                    cleaned_data["gp_practice_ods_code"] = ods_code
            except Exception as error:
                self.add_error("gp_practice_postcode", ValidationError(error))

        return cleaned_data
