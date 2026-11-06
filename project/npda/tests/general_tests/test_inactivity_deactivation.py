"""
Tests for deactivation of user accounts after a prolonged period of
inactivity (settings.ACCOUNT_INACTIVITY_DEACTIVATION_PERIOD_DAYS).

The check runs when credentials are validated at login:
- in production via CaptchaAuthenticationForm.confirm_login_allowed (the
  two-factor wizard's auth step)
- in local development via the 2FA/captcha bypass branch of
  RCPCHLoginView.post, which is exercised here with override_settings
"""

from datetime import timedelta
from http import HTTPStatus

import pytest
from django.core.exceptions import ValidationError
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from project.constants.user import AUDIT_CENTRE_COORDINATOR, AUDIT_CENTRE_EDITOR
from project.npda.forms.npda_user_form import CaptchaAuthenticationForm
from project.npda.general_functions.inactivity_deactivation import (
    get_inactivity_deactivation_message,
    is_inactive_beyond_deactivation_period,
)
from project.npda.models import NPDAUser, VisitActivity
from project.npda.tests.constants_for_tests import ALDER_HEY_PZ_CODE
from project.npda.tests.factories.npda_user_factory import NPDAUserFactory
from project.npda.tests.utils import login_and_verify_user

INACTIVITY_PERIOD_DAYS = 730


# is_inactive_beyond_deactivation_period


@pytest.mark.django_db
@override_settings(ACCOUNT_INACTIVITY_DEACTIVATION_PERIOD_DAYS=INACTIVITY_PERIOD_DAYS)
def test_recently_active_user_is_not_flagged_for_deactivation():
    user = NPDAUserFactory(
        role=AUDIT_CENTRE_EDITOR,
        last_login=timezone.now() - timedelta(days=30),
    )

    assert is_inactive_beyond_deactivation_period(user) is False


@pytest.mark.django_db
@override_settings(ACCOUNT_INACTIVITY_DEACTIVATION_PERIOD_DAYS=INACTIVITY_PERIOD_DAYS)
def test_user_inactive_beyond_period_is_flagged_for_deactivation():
    user = NPDAUserFactory(
        role=AUDIT_CENTRE_EDITOR,
        last_login=timezone.now() - timedelta(days=731),
    )

    assert is_inactive_beyond_deactivation_period(user) is True


@pytest.mark.django_db
@override_settings(ACCOUNT_INACTIVITY_DEACTIVATION_PERIOD_DAYS=INACTIVITY_PERIOD_DAYS)
def test_never_logged_in_user_flagged_if_account_created_beyond_period():
    user = NPDAUserFactory(
        role=AUDIT_CENTRE_EDITOR,
        last_login=None,
        date_joined=timezone.now() - timedelta(days=1000),
    )

    assert is_inactive_beyond_deactivation_period(user) is True


@pytest.mark.django_db
@override_settings(ACCOUNT_INACTIVITY_DEACTIVATION_PERIOD_DAYS=INACTIVITY_PERIOD_DAYS)
def test_never_logged_in_user_not_flagged_if_recently_joined():
    user = NPDAUserFactory(role=AUDIT_CENTRE_EDITOR, last_login=None)

    assert is_inactive_beyond_deactivation_period(user) is False


@pytest.mark.django_db
@override_settings(ACCOUNT_INACTIVITY_DEACTIVATION_PERIOD_DAYS=INACTIVITY_PERIOD_DAYS)
def test_superuser_never_flagged_for_deactivation():
    user = NPDAUserFactory(
        role=AUDIT_CENTRE_EDITOR,
        is_superuser=True,
        last_login=timezone.now() - timedelta(days=2000),
    )

    assert is_inactive_beyond_deactivation_period(user) is False


@pytest.mark.django_db
@override_settings(ACCOUNT_INACTIVITY_DEACTIVATION_PERIOD_DAYS=0)
def test_deactivation_check_disabled_when_period_is_zero():
    user = NPDAUserFactory(
        role=AUDIT_CENTRE_EDITOR,
        last_login=timezone.now() - timedelta(days=2000),
    )

    assert is_inactive_beyond_deactivation_period(user) is False


# CaptchaAuthenticationForm.confirm_login_allowed (production login path)


@pytest.mark.django_db
@override_settings(ACCOUNT_INACTIVITY_DEACTIVATION_PERIOD_DAYS=INACTIVITY_PERIOD_DAYS)
def test_confirm_login_allowed_deactivates_user_inactive_beyond_period(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
):
    user = NPDAUserFactory(
        role=AUDIT_CENTRE_EDITOR,
        last_login=timezone.now() - timedelta(days=800),
        organisation_employers=[ALDER_HEY_PZ_CODE],
    )

    form = CaptchaAuthenticationForm(request=None)

    with pytest.raises(ValidationError) as excinfo:
        form.confirm_login_allowed(user)

    assert "deactivated" in str(excinfo.value)

    user.refresh_from_db()
    assert user.is_active is False

    # An audit log entry records the deactivation and its reason
    deactivation_activity = VisitActivity.objects.filter(
        npdauser=user, activity=VisitActivity.ACCOUNT_DEACTIVATED_INACTIVITY
    ).get()
    assert "deactivated due to inactivity" in deactivation_activity.details
    assert VisitActivity.CHANGED_ADMIN_FLAG in VisitActivity.objects.filter(
        npdauser=user
    ).values_list("activity", flat=True)


@pytest.mark.django_db
@override_settings(ACCOUNT_INACTIVITY_DEACTIVATION_PERIOD_DAYS=INACTIVITY_PERIOD_DAYS)
def test_confirm_login_allowed_allows_recently_active_user(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
):
    user = NPDAUserFactory(
        role=AUDIT_CENTRE_EDITOR,
        last_login=timezone.now() - timedelta(days=30),
        organisation_employers=[ALDER_HEY_PZ_CODE],
    )

    form = CaptchaAuthenticationForm(request=None)
    form.confirm_login_allowed(user)  # should not raise

    user.refresh_from_db()
    assert user.is_active is True


@pytest.mark.django_db
@override_settings(SITE_CONTACT_EMAIL="npda@rcpch.ac.uk")
def test_deactivation_message_directs_user_to_the_npda_team():
    """
    The login page message is the only notification the user receives, so it
    must tell them how to get their account reactivated.
    """
    message = get_inactivity_deactivation_message()

    assert "deactivated due to inactivity" in message
    assert "npda@rcpch.ac.uk" in message


# RCPCHLoginView (local development 2FA/captcha bypass login path)


@pytest.mark.django_db
@override_settings(
    LOCAL_DEV_BYPASS_2FA_AND_CAPTCHA=True,
    ACCOUNT_INACTIVITY_DEACTIVATION_PERIOD_DAYS=INACTIVITY_PERIOD_DAYS,
)
def test_login_attempt_deactivates_user_inactive_beyond_period(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    user = NPDAUserFactory(
        role=AUDIT_CENTRE_EDITOR,
        last_login=timezone.now() - timedelta(days=800),
        organisation_employers=[ALDER_HEY_PZ_CODE],
    )

    response = client.post(
        reverse("login"),
        {"auth-username": user.email, "auth-password": "pw"},
        follow=True,
    )

    user.refresh_from_db()
    assert user.is_active is False

    # Sent back to the login page with a message about the deactivation
    assert response.redirect_chain[0][0] == reverse("login")
    messages_shown = [str(m) for m in response.context["messages"]]
    assert any("deactivated" in m for m in messages_shown)

    # A second attempt with valid credentials no longer authenticates
    assert client.login(username=user.email, password="pw") is False


@pytest.mark.django_db
@override_settings(
    LOCAL_DEV_BYPASS_2FA_AND_CAPTCHA=True,
    ACCOUNT_INACTIVITY_DEACTIVATION_PERIOD_DAYS=INACTIVITY_PERIOD_DAYS,
)
def test_login_succeeds_for_recently_active_user(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    user = NPDAUserFactory(
        role=AUDIT_CENTRE_EDITOR,
        last_login=timezone.now() - timedelta(days=30),
        organisation_employers=[ALDER_HEY_PZ_CODE],
    )

    response = client.post(
        reverse("login"),
        {"auth-username": user.email, "auth-password": "pw"},
        follow=True,
    )

    user.refresh_from_db()
    assert user.is_active is True

    # Logged in: not sent back to the login page
    assert response.redirect_chain[0][0] != reverse("login")
    assert response.status_code == 200


# Reactivation by a PDU coordinator


@pytest.mark.django_db
@override_settings(ACCOUNT_INACTIVITY_DEACTIVATION_PERIOD_DAYS=INACTIVITY_PERIOD_DAYS)
def test_coordinator_can_reactivate_user_deactivated_for_inactivity(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    """
    A user deactivated for inactivity, then reactivated by their PDU
    coordinator, must be able to log in again without being immediately
    re-deactivated.
    """
    coordinator = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=AUDIT_CENTRE_COORDINATOR,
    ).first()
    user = NPDAUserFactory(
        role=AUDIT_CENTRE_EDITOR,
        last_login=timezone.now() - timedelta(days=800),
        organisation_employers=[ALDER_HEY_PZ_CODE],
    )

    # The user's login attempt deactivates their account
    form = CaptchaAuthenticationForm(request=None)
    with pytest.raises(ValidationError):
        form.confirm_login_allowed(user)
    user.refresh_from_db()
    assert user.is_active is False

    # Their PDU coordinator reactivates them via the user update view
    client = login_and_verify_user(client, coordinator)
    response = client.post(
        reverse("npdauser-update", kwargs={"pk": user.pk}),
        data={"activate": "true"},
    )

    assert response.status_code == HTTPStatus.FOUND

    user.refresh_from_db()
    assert user.is_active is True
    assert user.reactivated_at is not None

    # The reactivation is recorded in the audit log, attributed to the coordinator
    reactivation_activity = (
        VisitActivity.objects.filter(
            npdauser=user, activity=VisitActivity.CHANGED_ADMIN_FLAG
        )
        .order_by("-activity_datetime")
        .first()
    )
    assert reactivation_activity is not None
    assert "is_active: 'False' → 'True'" in reactivation_activity.details
    assert reactivation_activity.npdauser_admin == coordinator

    # The inactivity check no longer flags them, so they can log in again
    assert is_inactive_beyond_deactivation_period(user) is False


@pytest.mark.django_db
@override_settings(ACCOUNT_INACTIVITY_DEACTIVATION_PERIOD_DAYS=INACTIVITY_PERIOD_DAYS)
def test_user_deactivated_again_if_inactive_beyond_period_after_reactivation(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
):
    """
    Reactivation restarts rather than disables the inactivity clock: a user
    who does not log in for another full period after being reactivated is
    deactivated again.
    """
    user = NPDAUserFactory(
        role=AUDIT_CENTRE_EDITOR,
        last_login=timezone.now() - timedelta(days=900),
        organisation_employers=[ALDER_HEY_PZ_CODE],
    )
    # Reactivated 800 days ago, and never logged in since
    user.reactivated_at = timezone.now() - timedelta(days=800)
    user.save()

    assert is_inactive_beyond_deactivation_period(user) is True


@pytest.mark.django_db
@override_settings(ACCOUNT_INACTIVITY_DEACTIVATION_PERIOD_DAYS=INACTIVITY_PERIOD_DAYS)
def test_recent_reactivation_overrides_older_last_login(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
):
    """
    The check measures from the most recent of last login and reactivation.
    """
    user = NPDAUserFactory(
        role=AUDIT_CENTRE_EDITOR,
        last_login=timezone.now() - timedelta(days=900),
        organisation_employers=[ALDER_HEY_PZ_CODE],
    )
    # Reactivated recently: the 900-day-old last login must not flag them
    user.reactivated_at = timezone.now() - timedelta(days=30)
    user.save()

    assert is_inactive_beyond_deactivation_period(user) is False
