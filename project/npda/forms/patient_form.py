# python imports
import logging
from datetime import date

# project imports
import nhs_number
# third-party imports
from dateutil.relativedelta import relativedelta
from django import forms
# django imports
from django.apps import apps
from django.core.exceptions import ValidationError
from requests import RequestException

from ...constants.styles.form_styles import *
from ..general_functions import (gp_details_for_ods_code,
                                 gp_ods_code_for_postcode, imd_for_postcode,
                                 validate_postcode)
from ..models import Patient
from ..validators import not_in_the_future_validator

logger = logging.getLogger(__name__)


class DateInput(forms.DateInput):
    input_type = "date"


class NHSNumberField(forms.CharField):
    def to_python(self, value):
        number = super().to_python(value)
        normalised = nhs_number.standardise_format(number)

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

    def clean_postcode(self):
        postcode = self.cleaned_data["postcode"]

        try:
            result = validate_postcode(postcode)

            if not result:
                self.add_error(
                    "postcode",
                    ValidationError("Invalid postcode %(postcode)s",
                        params={"postcode":postcode})
                )

                return postcode
            else:
                return result["normalised_postcode"]
        except RequestException as err:
            logger.warning(f"Error validating postcode {err}")
            return postcode

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
            self.add_error("gp_practice_ods_code", ValidationError("'GP Practice ODS code' and 'GP Practice postcode' cannot both be empty"))

        if gp_practice_postcode:
            try:
                validation_result = validate_postcode(gp_practice_postcode)
                normalised_postcode = validation_result["normalised_postcode"]

                ods_code = gp_ods_code_for_postcode(normalised_postcode)

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
                    cleaned_data["gp_practice_postcode"] = normalised_postcode
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
