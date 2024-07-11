# django
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.contrib.auth.base_user import BaseUserManager
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.gis.db import models
from django.db.models.functions import Lower
from django.contrib.gis.db.models import UniqueConstraint
from .organisation_employer import OrganisationEmployer

from ...constants import *
from ..general_functions import *


class NPDAUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.

    RCPCH Audit team members can be clinicians or RCPCH staff
    RCPCH staff cannot be associated with a organisation trust
    All clinicians must be associated with a organisation trust
    """

    def create_user(self, email, password, first_name, role, **extra_fields):
        """
        Create and save a User with the given email and password.
        """

        if not email:
            raise ValueError(_("You must provide an email address"))

        # if not extra_fields.get("organisation_employer") and not extra_fields.get(
        #     "is_rcpch_staff"
        # ):
        #     # Non-RCPCH staff (is_rcpch_staff) are not affiliated with a organisation
        #     raise ValueError(
        #         _("You must provide the name of your main organisation trust.")
        #     )

        if not role:
            raise ValueError(_("You must provide your role in the NPDA audit."))

        email = self.normalize_email(str(email))
        user = self.model(
            email=email,
            first_name=first_name,
            password=password,
            role=role,
            **extra_fields,
        )

        user.set_password(password)
        user.view_preference = 0  # organisation level view preference
        if not extra_fields.get("is_superuser"):
            user.is_superuser = False
        if not extra_fields.get("is_active"):
            user.is_active = False
        # user not active until has confirmed by email
        user.email_confirmed = False
        # set time password has been updated
        user.password_last_set = timezone.now()
        print(f"{user} password updated")
        user.save()

        """
        Allocate Groups - the groups already have permissions allocated
        """
        group = group_for_role(user.role)
        user.save()
        user.groups.add(group)

        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        # Organisation = apps.get_model("npda", "Organisation")

        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_rcpch_audit_team_member", True)
        extra_fields.setdefault("is_rcpch_staff", False)
        extra_fields.setdefault("email_confirmed", True)
        extra_fields.setdefault("password_last_set", timezone.now())
        # PDU level preference
        extra_fields.setdefault("view_preference", 1)

        if extra_fields.get("is_active") is not True:
            raise ValueError(_("Superuser must have is_active=True."))
        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        if extra_fields.get("role") not in [1, 2, 3, 4]:
            raise ValueError("--role must be an integer between 1 and 4")
        else:
            if extra_fields.get("role") == 4:
                extra_fields.setdefault("is_rcpch_staff", True)
                extra_fields.setdefault("view_preference", 2)  # national scope
                organisation_employer, created = (
                    OrganisationEmployer.objects.get_or_create(
                        ods_code="8HV48",
                        name="Royal College of Paediatrics and Child Health",
                    )
                )
            else:
                extra_fields.setdefault("is_rcpch_staff", False)
                extra_fields.setdefault("view_preference", 2)  # national scope
                organisation_employer, created = (
                    OrganisationEmployer.objects.get_or_create(
                        ods_code="RJZ01",
                        name="KING'S COLLEGE HOSPITAL (DENMARK HILL)",
                        pz_code="PZ215",
                    )
                )

        logged_in_user = self.create_user(email.lower(), password, **extra_fields)
        logged_in_user.organisation_employers.add(organisation_employer)

        """
        Allocate Roles
        """

        group = group_for_role(logged_in_user.role)
        logged_in_user.groups.add(group)
        return logged_in_user


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
    email = models.EmailField(
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
    view_preference = models.SmallIntegerField(
        choices=VIEW_PREFERENCES,
        default=0,  # Organisation level is default
        blank=False,
        null=False,
    )
    date_joined = models.DateTimeField(default=timezone.now)
    role = models.PositiveSmallIntegerField(choices=ROLES)
    email_confirmed = models.BooleanField(default=False)
    password_last_set = models.DateTimeField(default=timezone.now)

    REQUIRED_FIELDS = ["role", "first_name", "surname", "is_rcpch_audit_team_member"]
    USERNAME_FIELD = "email"

    objects = NPDAUserManager()

    organisation_employers = models.ManyToManyField(
        to=OrganisationEmployer,
        verbose_name=_("Employing organisation"),
        help_text=_("Enter your employing organisation"),
        related_name="organisation_employers",
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

    def get_all_employer_organisations(self):
        return self.organisation_employers.all()

    def __unicode__(self):
        return self.email

    def has_module_perms(self, app_label):
        return True

    def save(self, *args, **kwargs) -> None:
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
        permissions = [CAN_PUBLISH_NPDA_DATA, CAN_CONSENT_TO_AUDIT_PARTICIPATION]
        ordering = ("surname",)

    def __str__(self) -> str:
        return self.get_full_name()
