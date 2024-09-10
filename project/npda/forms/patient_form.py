# python imports
import logging

# django imports
from django.apps import apps
from django.core.exceptions import ValidationError
from django import forms

from requests import RequestException

# project imports
import nhs_number
from ..models import Patient
from ...constants.styles.form_styles import *
from ..general_functions import (
    validate_postcode,
    gp_ods_code_for_postcode,
    gp_details_for_ods_code,
    imd_for_postcode
)


logger = logging.getLogger(__name__)


class DateInput(forms.DateInput):
    input_type = "date"


class NHSNumberField(forms.CharField):
    def to_python(self, value):
        number = super().to_python(value)
        normalised = nhs_number.normalise_number(number)

        # For some combinations we get back an empty string (eg '719-573 0220')
        return normalised or value

    def validate(self, value):
        if not value:
            raise ValidationError('NHS number required')

        if not nhs_number.is_valid(value):
            raise ValidationError("Invalid NHS number")


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
        }

    def clean_postcode(self):
        if not self.cleaned_data["postcode"]:
            raise ValidationError("This field is required")

        postcode = (
            self.cleaned_data["postcode"].upper().replace(" ", "").replace("-", "")
        )
        
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
                    "'GP Practice ODS code' and 'GP Practice postcode' cannot both be empty"
                )
            )

        return cleaned_data


class PatientFormWithSynchronousValidators(PatientForm):
    def clean_postcode(self):
        super().clean_postcode()

        postcode = self.cleaned_data["postcode"]

        try:
            if not validate_postcode(postcode=postcode):
                self.add_error(
                    "postcode",
                    ValidationError("Invalid postcode %(postcode)s",
                        params={"postcode":postcode})
                )
        except RequestException as err:
            logger.warning(f"Error validating postcode {err}")

        return postcode
    
    def clean(self):
        cleaned_data = super().clean()
        gp_practice_ods_code = cleaned_data.get("gp_practice_ods_code")
        gp_practice_postcode = cleaned_data.get("gp_practice_postcode")

        if not gp_practice_ods_code and gp_practice_postcode:
            try:
                ods_code = gp_ods_code_for_postcode(gp_practice_postcode)

                if not ods_code:
                    self.add_error(
                        "gp_practice_postcode",
                        ValidationError(
                            "Could not find GP practice with postcode %(postcode)s",
                            params={"postcode":gp_practice_postcode}
                        )
                    )
                else:
                    cleaned_data["gp_practice_ods_code"] = ods_code
            except RequestException as err:
                logger.warning(f"Error looking up GP practice by postcode {err}")
        elif gp_practice_ods_code:
            try:
                if not gp_details_for_ods_code(gp_practice_ods_code):
                    self.add_error(
                        "gp_practice_ods_code",
                        ValidationError(
                            "Could not find GP practice with ODS code %(ods_code)s",
                            params={"ods_code":gp_practice_ods_code}
                        )
                    )
            except RequestException as err:
                logger.warning(f"Error looking up GP practice by ODS code {err}")

        return cleaned_data

    # TODO MRB: override save and move the imd lookup from the patient model