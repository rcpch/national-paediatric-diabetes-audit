from django import forms
from django.contrib.auth.forms import SetPasswordForm
from ..models import NPDAUser
from ...constants.styles.form_styles import *
import logging
from django.utils import timezone
from django.utils.translation import gettext as _

# Logging setup
logger = logging.getLogger(__name__)


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

class NPDAUpdatePasswordForm(SetPasswordForm):
    # form show when setting or resetting password
    # password validation occurs here and updates the password_last_set field
    is_admin = False

    def __init__(self, user, *args, **kwargs):
        self.user = user
        if (
            self.user.is_rcpch_audit_team_member
            or self.user.is_superuser
            or self.user.is_rcpch_staff
        ):
            self.is_admin = True
        super(SetPasswordForm, self).__init__(*args, **kwargs)

    def clean(self) -> dict[str]:
        if self.is_admin and len(super().clean()["new_password1"]) < 16:
            raise forms.ValidationError(
                {
                    "new_password2": _(
                        "RCPCH audit team members must have passwords of 16 characters or more."
                    )
                }
            )
        return super().clean()

    def save(self, *args, commit=True, **kwargs):
        user = super().save(*args, commit=False, **kwargs)
        user.password_last_set = timezone.now()
        if commit:
            logger.debug(f"Updating password_last_set to {timezone.now()}")
            user.save()
        return user