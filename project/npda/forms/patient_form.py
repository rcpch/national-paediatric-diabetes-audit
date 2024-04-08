from django import forms
from ..models import Patient


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
            "nhs_number": forms.TextInput(
                attrs={"hx-post": '{% url "patient-update" object.pk %}'}
            ),
            "sex": forms.TextInput(
                attrs={"hx-post": '{% url "patient-update" object.pk %}'}
            ),
            "date_of_birth": forms.TextInput(
                attrs={"hx-post": '{% url "patient-update" object.pk %}'}
            ),
            "postcode": forms.TextInput(
                attrs={"hx-post": '{% url "patient-update" object.pk %}'}
            ),
            "ethnicity": forms.TextInput(
                attrs={"hx-post": '{% url "patient-update" object.pk %}'}
            ),
            "diabetes_type": forms.TextInput(
                attrs={"hx-post": '{% url "patient-update" object.pk %}'}
            ),
            "diagnosis_date": forms.TextInput(
                attrs={"hx-post": '{% url "patient-update" object.pk %}'}
            ),
            "death_date": forms.TextInput(
                attrs={"hx-post": '{% url "patient-update" object.pk %}'}
            ),
            "gp_practice_ods_code": forms.TextInput(
                attrs={"hx-post": '{% url "patient-update" object.pk %}'}
            ),
            "gp_practice_postcode": forms.TextInput(
                attrs={"hx-post": '{% url "patient-update" object.pk %}'}
            ),
        }
