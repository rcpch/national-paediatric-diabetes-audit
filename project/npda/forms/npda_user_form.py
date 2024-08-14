# python imports
import logging

# django imports
from django.apps import apps
from django.conf import settings
from django.contrib.auth.forms import SetPasswordForm, AuthenticationForm
from django import forms
from django.utils import timezone
from django.utils.translation import gettext as _

# third party imports
from captcha.fields import CaptchaField

from project.npda.general_functions import organisations_adapter

# RCPCH imports
from ...constants.styles.form_styles import *
from ..models import NPDAUser
from project.npda.general_functions import (
    organisations_adapter,
)


# Logging setup
logger = logging.getLogger(__name__)


class NPDAUserForm(forms.ModelForm):

    add_employer = forms.ChoiceField(
        choices=[],  # Initially empty, will be populated dynamically
        required=False,
        widget=forms.Select(attrs={"class": SELECT}),
        label="Add Employer",
    )

    organisation_choices = []

    class Meta:
        model = NPDAUser
        fields = [
            "title",
            "first_name",
            "surname",
            "email",
            "is_staff",
            "is_superuser",
            "is_rcpch_audit_team_member",
            "is_rcpch_staff",
            "role",
            "add_employer",
        ]
        widgets = {
            "title": forms.Select(attrs={"class": SELECT}),
            "first_name": forms.TextInput(attrs={"class": TEXT_INPUT}),
            "surname": forms.TextInput(attrs={"class": TEXT_INPUT}),
            "email": forms.EmailInput(attrs={"class": TEXT_INPUT}),
            "is_staff": forms.CheckboxInput(attrs={"class": "accent-rcpch_pink"}),
            "is_superuser": forms.CheckboxInput(attrs={"class": "accent-rcpch_pink"}),
            "is_rcpch_audit_team_member": forms.CheckboxInput(
                attrs={"class": "accent-rcpch_pink"}
            ),
            "is_rcpch_staff": forms.CheckboxInput(attrs={"class": "accent-rcpch_pink"}),
            "role": forms.Select(attrs={"class": SELECT}),
            "add_employer": forms.Select(
                attrs={
                    "class": SELECT,
                    "required": False,
                    "name": "add_employer",
                    "id": "id_add_employer",
                }
            ),
        }

    def __init__(self, *args, **kwargs) -> None:
        PaediatricDiabetesUnit = apps.get_model("npda", "PaediatricDiabetesUnit")
        OrganisationEmployer = apps.get_model("npda", "OrganisationEmployer")

        # get the request object from the kwargs
        self.request = kwargs.pop("request", None)

        super().__init__(*args, **kwargs)
        self.fields["title"].required = False
        self.fields["first_name"].required = True
        self.fields["surname"].required = True
        self.fields["email"].required = True
        self.fields["role"].required = True
        self.fields["add_employer"].required = False

        # only if the form is bound - this user is being updated
        if self.instance.pk is not None:
            # this is a bit of a hack but necessary due to htmx.
            # The add_employer field is not part of the model, so we need to remove it from the data dictionary
            # in a bound form on form submission, so that the form will validate correctly
            # the add employer work flow happens via htmx and not form submission
            self.data = self.data.copy()
            self.data.pop("add_employer", None)

        elif self.request.POST:
            # this is a create request - the form is being submitted
            # we need to remove the selection from the add_employer field and use this to create the employer relationship
            # but only if the form is valid
            ods_code = self.data.get("add_employer")
            # remove the add_employer field from the data dictionary
            # as it is immutable we need to copy it first
            self.data = self.data.copy()
            self.data.pop("add_employer", None)

            if ods_code and self.is_valid():
                # the form is filled out correctly and the user has selected an employer
                # we need to create the employer relationship - since this is a new user,
                # this organisation will be the user's primary employer
                pdu_object = organisations_adapter.get_single_pdu_from_ods_code(
                    ods_code
                )
                pdu, created = PaediatricDiabetesUnit.objects.update_or_create(
                    ods_code=ods_code, pz_code=pdu_object.pz_code
                )
                npda_user = self.instance
                npda_user.save()
                OrganisationEmployer.objects.update_or_create(
                    npda_user=npda_user,
                    paediatric_diabetes_unit=pdu,
                    is_primary_employer=True,
                )


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


# IF IN DEBUG MODE, PRE-FILL CAPTCHA VALUE
class DebugCaptchaField(CaptchaField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget.widgets[-1].attrs["value"] = "DEBUGMODE"


class CaptchaAuthenticationForm(AuthenticationForm):
    captcha = DebugCaptchaField() if settings.DEBUG else CaptchaField()

    def __init__(self, request, *args, **kwargs) -> None:
        super().__init__(request, *args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": TEXT_INPUT})
        self.fields["password"].widget.attrs.update({"class": TEXT_INPUT})
        self.fields["captcha"].widget.attrs.update({"class": TEXT_INPUT})

        # If in DEBUG -> don't require captch, pre fill fields
        if settings.DEBUG:
            logger.warning(
                f"IN LOCAL DEVELOPMENT, BYPASSING LOGIN BY PREFILLING FIELDS"
            )
            self.fields["username"].widget.attrs["value"] = (
                settings.LOCAL_DEV_ADMIN_EMAIL
                or "SET LOCAL DEV ADMIN EMAIL IN ENVIRONMENT VARIABLES"
            )
            self.fields["password"].widget.attrs["value"] = (
                settings.LOCAL_DEV_ADMIN_PASSWORD
                or "SET LOCAL DEV ADMIN PASSWORD IN ENVIRONMENT VARIABLES"
            )
            self.fields["captcha"].required = False

    def clean_username(self) -> dict[str]:
        email = super().clean()["username"]
        if email:
            try:
                user = NPDAUser.objects.get(email=email.lower()).DoesNotExist
            except NPDAUser.DoesNotExist:
                return super().clean()

            user = NPDAUser.objects.get(email=email.lower())

            # visit_activities = VisitActivity.objects.filter(
            #     npda12user=user
            # ).order_by("-activity_datetime")[:5]

            # failed_login_activities = [
            #     activity for activity in visit_activities if activity.activity == 2
            # ]

            # if failed_login_activities:
            #     first_activity = failed_login_activities[-1]

            #     if len(
            #         failed_login_activities
            #     ) >= 5 and timezone.now() <= first_activity.activity_datetime + timezone.timedelta(
            #         minutes=10
            #     ):
            #         raise forms.ValidationError(
            #             "You have failed to login 5 or more consecutive times. You have been locked out for 10 minutes"
            #         )
            return email.lower()
