"""
Deactivation of user accounts after a prolonged period of inactivity.

Users who have not logged in for longer than
`settings.ACCOUNT_INACTIVITY_DEACTIVATION_PERIOD_DAYS` days are deactivated
the next time they attempt to log in. They are told what has happened on the
login page and emailed the contact details of their PDU coordinators so they
can request reactivation.
"""

import logging
from datetime import timedelta

from django.apps import apps
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils import timezone

from ...constants import AUDIT_CENTRE_COORDINATOR
from .email import send_email_to_recipients
from .ip_address import get_client_ip

logger = logging.getLogger(__name__)

EMAIL_TEMPLATE_NAME = "registration/account_deactivated_inactivity_email.html"

# Fallback contact address used in the login page message and the
# deactivation email if SITE_CONTACT_EMAIL is not set
DEFAULT_CONTACT_EMAIL = "npda@rcpch.ac.uk"


def get_site_contact_email() -> str:
    return getattr(settings, "SITE_CONTACT_EMAIL", None) or DEFAULT_CONTACT_EMAIL


def get_inactivity_deactivation_message() -> str:
    """
    The message shown on the login page to users whose account has been
    deactivated due to inactivity.
    """
    return (
        "Your account has been deactivated due to inactivity. "
        "We have emailed you the contact details of your PDU coordinator(s), "
        "who can reactivate your account. "
        f"Alternatively, contact the NPDA team at {get_site_contact_email()}."
    )


def get_last_login_datetime(user):
    """
    The user's last login, falling back to the date their account was created
    if they have never logged in.
    """
    return user.last_login or user.date_joined


def get_last_activity_datetime(user):
    """
    The reference time for the inactivity deactivation check: the user's last
    login (or the date their account was created if they have never logged
    in), or the time they were last reactivated by an administrator, whichever
    is later. Reactivation restarts the clock so that a user reactivated by
    their PDU coordinator is not immediately re-deactivated at their next
    login attempt.
    """
    last_activity = get_last_login_datetime(user)

    if user.reactivated_at and user.reactivated_at > last_activity:
        last_activity = user.reactivated_at

    return last_activity


def is_inactive_beyond_deactivation_period(user) -> bool:
    """
    Whether the user has been inactive for longer than
    settings.ACCOUNT_INACTIVITY_DEACTIVATION_PERIOD_DAYS days.

    Superusers are never deactivated automatically, and a period of zero (or
    less) disables the check entirely.
    """
    if settings.ACCOUNT_INACTIVITY_DEACTIVATION_PERIOD_DAYS <= 0:
        return False

    if user.is_superuser:
        return False

    last_activity = get_last_activity_datetime(user)
    if last_activity is None:
        return False

    return timezone.now() - last_activity > timedelta(
        days=settings.ACCOUNT_INACTIVITY_DEACTIVATION_PERIOD_DAYS
    )


def get_pdu_coordinators(user):
    """
    Active audit centre coordinators in the user's PDU(s), excluding the user
    themselves.
    """
    NPDAUser = apps.get_model("npda", "NPDAUser")

    return (
        NPDAUser.objects.filter(
            role=AUDIT_CENTRE_COORDINATOR,
            is_active=True,
            organisation_employers__in=user.organisation_employers.all(),
        )
        .exclude(pk=user.pk)
        .distinct()
    )


def construct_account_deactivated_email(user, request=None) -> str:
    """
    Renders the email sent to users deactivated due to inactivity, containing
    the contact details of their PDU coordinators.
    """
    context = {
        "user": user,
        "coordinators": get_pdu_coordinators(user),
        "last_login_datetime": get_last_login_datetime(user),
        "inactivity_period_days": settings.ACCOUNT_INACTIVITY_DEACTIVATION_PERIOD_DAYS,
        "site_contact_email": get_site_contact_email(),
    }

    if request is not None:
        site = get_current_site(request)
        context["domain"] = site.domain
        context["protocol"] = "https" if request.is_secure() else "http"

    return render_to_string(EMAIL_TEMPLATE_NAME, context)


def deactivate_user_for_inactivity(user, request=None) -> None:
    """
    Deactivates the user and emails them the contact details of their PDU
    coordinators so they can request reactivation.
    """
    user.is_active = False
    user.save()

    # The is_active change is also picked up by the user change signals
    # (logged as "Superuser or admin status changed"); this entry records
    # the reason explicitly.
    VisitActivity = apps.get_model("npda", "VisitActivity")
    VisitActivity.objects.create(
        npdauser=user,
        activity=VisitActivity.ACCOUNT_DEACTIVATED_INACTIVITY,
        ip_address=get_client_ip(request),
        details=(
            "Account automatically deactivated due to inactivity: no login for more "
            f"than {settings.ACCOUNT_INACTIVITY_DEACTIVATION_PERIOD_DAYS} days. "
            f"Last login: {user.last_login or 'Never'}."
        ),
    )

    logger.warning(
        "User %s deactivated due to inactivity (last activity %s)",
        user.email,
        get_last_activity_datetime(user),
    )

    try:
        send_email_to_recipients(
            recipients=[user.email],
            subject="Your National Paediatric Diabetes Audit account has been deactivated",
            message=construct_account_deactivated_email(user, request=request),
        )
    except Exception:
        logger.exception("Failed to send account deactivation email to %s", user.email)
