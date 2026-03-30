# django
import citext
from django.apps import apps
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.contrib.gis.db import models
from django.contrib.gis.db.models import UniqueConstraint
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ...constants import *
from ..general_functions import *
from ..logging import get_current_user


def title_to_choice(title_to_find):
    if not title_to_find:
        return None

    for choice, title in TITLES:
        if title_to_find.lower() == title.lower():
            return choice
    return None


class NPDAUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.

    RCPCH Audit team members can be clinicians or RCPCH staff
    RCPCH staff cannot be associated with a organisation trust
    All clinicians must be associated with a organisation trust
    """

    def create_or_update_user(
        self, email, password, role, pz_code, is_primary_employer=False, **extra_fields
    ):
        """
        Create and save a User with the given email and password.
        Note this is only used for creating dev user or importing users currently.
        It is called by create_superuser
        """
        PaediatricDiabetesUnit = apps.get_model("npda", "PaediatricDiabetesUnit")
        OrganisationEmployer = apps.get_model("npda", "OrganisationEmployer")

        if not email:
            raise ValueError(_("You must provide an email address"))

        if not role:
            raise ValueError(_("You must provide your role in the NPDA audit."))

        pdu = PaediatricDiabetesUnit.objects.get(pz_code=pz_code)

        email = self.normalize_email(str(email))

        user = self.filter(email=email).first()

        if not user:
            user = self.model(
                email=email,
                password=password,
                role=role,
                **extra_fields,
            )

            if password:
                user.set_password(password)
            else:
                user.set_unusable_password()

            user.password_last_set = timezone.now()
            user.date_joined = timezone.now()

        if extra_fields.get("title"):
            user.title = title_to_choice(extra_fields.get("title"))
        else:
            user.title = None
        if not extra_fields.get("is_superuser"):
            user.is_superuser = False
        if not extra_fields.get("is_active"):
            user.is_active = False
        if not extra_fields.get("is_staff"):
            user.is_staff = False
        if not extra_fields.get("is_rcpch_audit_team_member"):
            user.is_rcpch_audit_team_member = False
        if not extra_fields.get("is_rcpch_staff"):
            user.is_rcpch_staff = False
        if not extra_fields.get("is_patient_or_carer"):
            user.is_patient_or_carer = False
        # user not active until has confirmed by email
        if not extra_fields.get("email_confirmed"):
            user.email_confirmed = False

        user.save()

        """
        Allocate Groups - the groups already have permissions allocated
        """
        group = group_for_role(user.role)
        user.save()
        user.groups.add(group)

        # Attach PDU
        if not OrganisationEmployer.objects.filter(
            paediatric_diabetes_unit=pdu,
            npda_user=user,
        ).exists():
            # create the organisation employer
            OrganisationEmployer.objects.create(
                paediatric_diabetes_unit=pdu,
                npda_user=user,
                is_primary_employer=is_primary_employer,
            )

        return user

    def create_superuser(self, first_name, surname, email, password):
        return self.create_or_update_user(
            pz_code="PZ999",  # RCPCH
            email=email.lower(),
            password=password,
            first_name=first_name,
            last_name=surname,
            role=RCPCH_AUDIT_TEAM,
            is_superuser=True,
            is_active=True,
            is_staff=True,
            is_rcpch_audit_team_member=True,
            is_rcpch_staff=True,
            email_confirmed=True,
            is_primary_employer=True,
        )


class NPDAUser(AbstractUser, PermissionsMixin):
    username = None
    first_name = models.CharField(
        _("First name"),
        help_text=_("Enter your first name"),
        max_length=150,
        null=True,
        blank=True,
    )
    surname = models.CharField(
        _("Surname"),
        help_text=_("Enter your surname"),
        max_length=150,
        null=True,
        blank=True,
    )
    title = models.PositiveSmallIntegerField(choices=TITLES, blank=True, null=True)
    email = citext.CIEmailField(
        _("Email address"),
        help_text=_("Enter your email address."),
        unique=True,
        error_messages={"unique": _("This email address is already in use.")},
    )
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(
        # reflects if user has access to admin
        default=False
    )
    is_superuser = models.BooleanField(default=False)
    is_rcpch_audit_team_member = models.BooleanField(
        # reflects is a member of the RCPCH audit team. If is_rcpch_audit_team_member is True and
        # is_rcpch_staff is False, user is also a clinician/organisation admin and therefore must
        # may be affiliated with a organisation trust
        default=False
    )
    is_rcpch_staff = models.BooleanField(
        # reflects if user is an RCPCH employee
        # Any non-RCPCH staff must be affiliated with an organisation
        default=False
    )
    is_patient_or_carer = models.BooleanField(
        # reflects is a patient or carer
        # must be affiliated with an organisation
        default=False
    )
    date_joined = models.DateTimeField(default=timezone.now)
    role = models.PositiveSmallIntegerField(choices=ROLES)
    email_confirmed = models.BooleanField(default=False)
    password_last_set = models.DateTimeField(default=timezone.now)
    feature_flags = models.JSONField(default=list, blank=True)

    REQUIRED_FIELDS = ["role", "first_name", "surname", "is_rcpch_audit_team_member"]
    USERNAME_FIELD = "email"

    objects = NPDAUserManager()

    organisation_employers = models.ManyToManyField(
        to="npda.PaediatricDiabetesUnit",
        verbose_name=_("Employing organisation"),
        help_text=_("Enter your employing organisation"),
        through="npda.OrganisationEmployer",
    )

    created_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_users",
        verbose_name=_("Created by"),
        help_text=_("The user who created this account"),
    )

    updated_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_users",
        verbose_name=_("Updated by"),
        help_text=_("The user who last updated this account"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True,
        verbose_name=_("Created at"),
        help_text=_("The date and time this account was created"),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        null=True,
        blank=True,
        verbose_name=_("Updated at"),
        help_text=_("The date and time this account was last updated"),
    )

    def get_full_name(self):
        title = self.get_title_display()
        concatenated_name = ""
        if title:
            concatenated_name += f"{title} "
        if self.first_name:
            concatenated_name += f"{self.first_name} "
        if self.surname:
            concatenated_name += f"{self.surname}"
        return concatenated_name

    def get_short_name(self):
        return self.first_name

    def number_of_pdu_memberships(self):
        return self.organisation_employers.count()

    def get_all_employer_organisations(self):
        return self.organisation_employers.all()

    def user_roles(self):
        roles = []
        if self.is_rcpch_audit_team_member:
            roles.append("RCPCH Audit Team Member")
        if self.is_rcpch_staff:
            roles.append("RCPCH Staff")
        if self.is_patient_or_carer:
            roles.append("Patient or Carer")
        if self.role == RCPCH_AUDIT_TEAM:
            roles.append("RCPCH Audit Team")
        return ", ".join(roles)

    def user_groups(self):
        """
        Returns a list of group names the user belongs to.
        """
        return [group.name for group in self.groups.all()]

    def user_groups_readable(self):
        """
        Returns a readable string of group names the user belongs to.
        """

        group_keys = self.user_groups()
        if not group_keys:
            return "No groups"
        readable_names = [READABLE_GROUPNAMES.get(group, group) for group in group_keys]
        return ", ".join(readable_names)

    def primary_pdu(self):
        OrganisationEmployer = apps.get_model("npda", "OrganisationEmployer")

        # There should only be one primary organisation
        return OrganisationEmployer.objects.get(
            npda_user=self, is_primary_employer=True
        ).paediatric_diabetes_unit

    def __unicode__(self):
        return self.email

    def has_module_perms(self, app_label):
        return True

    def save(self, current_user=None, *args, **kwargs) -> None:
        # save method override to set the created_by and updated_by fields
        # if the user is authenticated, otherwise these fields will not be set
        # relies on the get_current_user middleware function to retrieve the current user
        # from local thread storage
        # This method also sets the email_confirmed field to True if the user has a usable password
        # as new users are created with an unusable password by default and this is used to flag
        # that they have not yet confirmed their email address.
        user_creating_or_updating_user = current_user or get_current_user()
        # Set created_by and updated_by. Note that the created_at and updated_at fields
        # are automatically set by Django when the model is saved, so we don't need to set
        if (
            user_creating_or_updating_user
            and user_creating_or_updating_user.is_authenticated
        ):
            if not self.pk:
                # If this is a new record, set the created_by field
                self.created_by = user_creating_or_updating_user
            self.updated_by = user_creating_or_updating_user

        if self.has_usable_password() and not self.email_confirmed:
            self.email_confirmed = True
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = "NPDA User"
        verbose_name_plural = "NPDA Users"
        constraints = [
            UniqueConstraint(
                Lower("email"),
                name="user_email_ci_uniqueness",
            ),
        ]
        permissions = [
            CAN_PUBLISH_NPDA_DATA,
            CAN_CONSENT_TO_AUDIT_PARTICIPATION,
            CAN_SUBMIT_CSV,
            CAN_DOWNLOAD_CSV,
        ]
        ordering = ("surname",)

    def __str__(self) -> str:
        return self.get_full_name()
