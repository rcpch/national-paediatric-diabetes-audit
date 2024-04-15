from django import forms
from ..models import Patient
from ...constants.styles.form_styles import *


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
        widgets = {
            "nhs_number": forms.TextInput(attrs={"class": TEXT_INPUT}),
            "sex": forms.Select(attrs={"class": SELECT}),
            "date_of_birth": forms.DateInput(
                format="%Y-%m-%d", attrs={"class": DATE_INPUT}
            ),
            "postcode": forms.TextInput(attrs={"class": TEXT_INPUT}),
            "ethnicity": forms.Select(attrs={"class": SELECT}),
            "diabetes_type": forms.Select(attrs={"class": SELECT}),
            "diagnosis_date": forms.DateInput(
                format="%Y-%m-%d", attrs={"class": DATE_INPUT}
            ),
            "death_date": forms.DateInput(
                format="%Y-%m-%d", attrs={"class": DATE_INPUT}
            ),
            "gp_practice_ods_code": forms.TextInput(attrs={"class": TEXT_INPUT}),
            "gp_practice_postcode": forms.TextInput(attrs={"class": TEXT_INPUT}),
        }
