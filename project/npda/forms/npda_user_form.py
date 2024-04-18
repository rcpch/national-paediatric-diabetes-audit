from django import forms
from django.core.exceptions import ValidationError
from ..models import NPDAUser
from ...constants.styles.form_styles import *


class NPDAUserForm(forms.ModelForm):
    
    class Meta:
        model = NPDAUser
        fields = [
            'title',
            'first_name',
            'surname',
            'email',
            'is_staff',
            'is_superuser',
            'is_rcpch_audit_team_member',
            'is_rcpch_staff',
            'role',
            'organisation_employer'
        ]
        widgets = {
            'title': forms.Select(attrs={"class": SELECT}),
            'first_name': forms.TextInput(attrs={"class": TEXT_INPUT}),
            'surname':forms.TextInput(attrs={"class": TEXT_INPUT}),
            'email': forms.EmailInput(attrs={"class": TEXT_INPUT}),
            'is_staff':forms.CheckboxInput(attrs={"class": "accent-rcpch_pink"}),
            'is_superuser':forms.CheckboxInput(attrs={"class": "accent-rcpch_pink"}),
            'is_rcpch_audit_team_member':forms.CheckboxInput(attrs={"class": "accent-rcpch_pink"}),
            'is_rcpch_staff':forms.CheckboxInput(attrs={"class": "accent-rcpch_pink"}),
            'role':forms.Select(attrs={"class": SELECT}),
            'organisation_employer':forms.Select(attrs={"class": SELECT}),
        }