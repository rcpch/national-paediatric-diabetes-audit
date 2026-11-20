"""
Tests for signing in with Microsoft Entra ID, and for the
ENTRA_ID_LOGIN_REQUIRED_FOR_RCPCH_STAFF setting that makes it compulsory for
superusers and the RCPCH Audit Team.

Microsoft is never contacted: the msal client is replaced with a fake that
returns the ID token claims we choose.
"""

from http import HTTPStatus
from unittest.mock import patch

import pytest
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.test import override_settings
from django.urls import reverse
from django_otp import DEVICE_ID_SESSION_KEY
from django_otp.plugins.otp_totp.models import TOTPDevice

from project.constants import AUDIT_CENTRE_EDITOR, RCPCH_AUDIT_TEAM
from project.npda.forms.npda_user_form import CaptchaAuthenticationForm
from project.npda.general_functions.entra_id import (
    ENTRA_ID_LOGIN_REQUIRED_MESSAGE,
    may_use_entra_id_login,
    must_use_entra_id_login,
)
from project.npda.models import EntraIDDevice, NPDAUser, VisitActivity
from project.npda.tests.factories.npda_user_factory import NPDAUserFactory
from project.npda.tests.utils import twofactor_signin
from project.npda.views.entra_id import (
    ENTRA_ID_FLOW_SESSION_KEY,
    ENTRA_ID_NEXT_SESSION_KEY,
)

TENANT_ID = "11111111-2222-3333-4444-555555555555"
OBJECT_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
PASSWORD = "A-Valid-Password-1!"

ENTRA_CONFIGURED = {
    "ENTRA_ID_TENANT_ID": TENANT_ID,
    "ENTRA_ID_CLIENT_ID": "client-id",
    "ENTRA_ID_CLIENT_SECRET": "client-secret",
    "ENTRA_ID_LOGIN_ENABLED": True,
}
ENTRA_REQUIRED = {**ENTRA_CONFIGURED, "ENTRA_ID_LOGIN_REQUIRED_FOR_RCPCH_STAFF": True}
ENTRA_OPTIONAL = {**ENTRA_CONFIGURED, "ENTRA_ID_LOGIN_REQUIRED_FOR_RCPCH_STAFF": False}


class FakeEntraClient:
    """Stands in for msal.ConfidentialClientApplication."""

    def __init__(self, result=None, raises=None):
        self.result = result
        self.raises = raises
        self.redeemed_with = None

    def initiate_auth_code_flow(self, scopes, redirect_uri, prompt):
        self.redirect_uri = redirect_uri
        return {
            "auth_uri": "https://login.microsoftonline.com/authorize?state=abc",
            "state": "abc",
        }

    def acquire_token_by_auth_code_flow(self, flow, auth_response):
        self.redeemed_with = (flow, auth_response)
        if self.raises:
            raise self.raises
        return self.result


def claims_for(email, tid=TENANT_ID, oid=OBJECT_ID):
    return {"id_token_claims": {"tid": tid, "oid": oid, "preferred_username": email}}


def complete_entra_sign_in(client, fake_client, next_url=None):
    session = client.session
    session[ENTRA_ID_FLOW_SESSION_KEY] = {"state": "abc"}
    if next_url:
        session[ENTRA_ID_NEXT_SESSION_KEY] = next_url
    session.save()

    with patch(
        "project.npda.views.entra_id.build_entra_id_client",
        return_value=fake_client,
    ):
        return client.get(
            reverse("entra_id_callback"), {"code": "the-code", "state": "abc"}
        )


def make_user(**kwargs):
    user = NPDAUserFactory(**kwargs)
    user.set_password(PASSWORD)
    user.save()
    return user


@pytest.fixture
def superuser(seed_groups_fixture):
    return make_user(
        role=RCPCH_AUDIT_TEAM, is_superuser=True, email="super@rcpch.ac.uk"
    )


@pytest.fixture
def audit_team_member(seed_groups_fixture):
    return make_user(role=RCPCH_AUDIT_TEAM, email="audit.team@rcpch.ac.uk")


@pytest.fixture
def clinician(seed_groups_fixture):
    return make_user(role=AUDIT_CENTRE_EDITOR, email="clinician@nhs.net")


def password_login(client, user):
    """Sign in with email and password, as the CI environment does."""
    return client.post(
        reverse("two_factor:login"),
        {
            "rcpch_login_view-current_step": "auth",
            "auth-username": user.email,
            "auth-password": PASSWORD,
            "auth-captcha_0": "x",
            "auth-captcha_1": "PASSED",
        },
    )


# Who the setting covers


@pytest.mark.django_db
def test_superusers_and_audit_team_may_use_entra_id(
    superuser, audit_team_member, clinician
):
    assert may_use_entra_id_login(superuser)
    assert may_use_entra_id_login(audit_team_member)
    assert not may_use_entra_id_login(clinician)


@pytest.mark.django_db
def test_superuser_with_clinician_role_may_use_entra_id(seed_groups_fixture):
    user = make_user(role=AUDIT_CENTRE_EDITOR, is_superuser=True)

    assert may_use_entra_id_login(user)


@pytest.mark.django_db
def test_entra_id_only_compulsory_when_setting_is_on(superuser, clinician):
    with override_settings(ENTRA_ID_LOGIN_REQUIRED_FOR_RCPCH_STAFF=False):
        assert not must_use_entra_id_login(superuser)

    with override_settings(ENTRA_ID_LOGIN_REQUIRED_FOR_RCPCH_STAFF=True):
        assert must_use_entra_id_login(superuser)
        assert not must_use_entra_id_login(clinician)


# Password login (CaptchaAuthenticationForm.confirm_login_allowed)


@pytest.mark.django_db
@override_settings(**ENTRA_REQUIRED)
@pytest.mark.parametrize("user_fixture", ["superuser", "audit_team_member"])
def test_password_login_refused_for_rcpch_staff_when_required(request, user_fixture):
    user = request.getfixturevalue(user_fixture)
    TOTPDevice.objects.create(user=user, name="default")
    password_hash = user.password

    form = CaptchaAuthenticationForm(request=None)
    with pytest.raises(ValidationError) as excinfo:
        form.confirm_login_allowed(user)

    assert excinfo.value.code == "entra_id_required"
    assert "sign in with Microsoft" in str(excinfo.value)

    refused = VisitActivity.objects.get(
        npdauser=user, activity=VisitActivity.UNSUCCESSFUL_LOGIN
    )
    assert "Entra ID" in refused.details

    # Credentials are left in place so the setting can be switched off again
    user.refresh_from_db()
    assert user.password == password_hash
    assert user.check_password(PASSWORD)
    assert TOTPDevice.objects.filter(user=user, name="default").exists()


@pytest.mark.django_db
@override_settings(**ENTRA_OPTIONAL)
def test_password_login_allowed_for_rcpch_staff_when_not_required(superuser):
    form = CaptchaAuthenticationForm(request=None)

    form.confirm_login_allowed(superuser)  # does not raise


@pytest.mark.django_db
@override_settings(**ENTRA_REQUIRED)
def test_password_login_allowed_for_clinicians_when_required(clinician):
    form = CaptchaAuthenticationForm(request=None)

    form.confirm_login_allowed(clinician)  # does not raise


@pytest.mark.django_db
@override_settings(LOCAL_DEV_BYPASS_2FA_AND_CAPTCHA=False, **ENTRA_REQUIRED)
def test_password_login_view_refuses_rcpch_staff_when_required(client, superuser):
    with patch("captcha.conf.settings.CAPTCHA_TEST_MODE", True):
        response = password_login(client, superuser)

    assert response.status_code == HTTPStatus.OK
    assert response.context["form"].non_field_errors() == [
        ENTRA_ID_LOGIN_REQUIRED_MESSAGE
    ]
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
@override_settings(LOCAL_DEV_BYPASS_2FA_AND_CAPTCHA=False, **ENTRA_REQUIRED)
def test_password_login_view_refusal_does_not_reveal_whether_password_is_right(
    client, superuser
):
    with patch("captcha.conf.settings.CAPTCHA_TEST_MODE", True):
        with patch(
            "django.contrib.auth.forms.authenticate", wraps=authenticate
        ) as checked_password:
            response = client.post(
                reverse("two_factor:login"),
                {
                    "rcpch_login_view-current_step": "auth",
                    "auth-username": superuser.email.upper(),
                    "auth-password": "the-wrong-password",
                    "auth-captcha_0": "x",
                    "auth-captcha_1": "PASSED",
                },
            )

    # Refused with the same message as for the right password, before the
    # password is checked at all
    assert response.context["form"].non_field_errors() == [
        ENTRA_ID_LOGIN_REQUIRED_MESSAGE
    ]
    checked_password.assert_not_called()
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
@override_settings(LOCAL_DEV_BYPASS_2FA_AND_CAPTCHA=True, **ENTRA_REQUIRED)
def test_local_dev_bypass_login_refuses_rcpch_staff_when_required(client, superuser):
    response = password_login(client, superuser)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse("two_factor:login")
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
@override_settings(LOCAL_DEV_BYPASS_2FA_AND_CAPTCHA=True, **ENTRA_OPTIONAL)
def test_local_dev_bypass_login_allows_rcpch_staff_when_not_required(client, superuser):
    response = password_login(client, superuser)

    assert response.status_code == HTTPStatus.FOUND
    assert int(client.session["_auth_user_id"]) == superuser.pk


# Login page


@pytest.mark.django_db
@override_settings(**ENTRA_OPTIONAL)
def test_login_page_offers_sign_in_with_microsoft_when_configured(client):
    response = client.get(reverse("two_factor:login"))

    assert b"Sign in with Microsoft" in response.content


@pytest.mark.django_db
@override_settings(ENTRA_ID_LOGIN_ENABLED=False)
def test_login_page_hides_sign_in_with_microsoft_when_not_configured(client):
    response = client.get(reverse("two_factor:login"))

    assert b"Sign in with Microsoft" not in response.content


@pytest.mark.django_db
@override_settings(ENTRA_ID_LOGIN_ENABLED=False)
def test_entra_id_routes_404_when_not_configured(client):
    assert client.get(reverse("entra_id_login")).status_code == HTTPStatus.NOT_FOUND
    assert client.get(reverse("entra_id_callback")).status_code == HTTPStatus.NOT_FOUND


# Starting the sign in


@pytest.mark.django_db
@override_settings(**ENTRA_OPTIONAL)
def test_entra_id_login_redirects_to_microsoft_and_keeps_safe_next(client):
    fake = FakeEntraClient()
    with patch("project.npda.views.entra_id.build_entra_id_client", return_value=fake):
        response = client.get(reverse("entra_id_login"), {"next": "/admin/"})

    assert response.status_code == HTTPStatus.FOUND
    assert response.url.startswith("https://login.microsoftonline.com/")
    assert fake.redirect_uri.endswith(reverse("entra_id_callback"))
    assert client.session[ENTRA_ID_FLOW_SESSION_KEY]["state"] == "abc"
    assert client.session[ENTRA_ID_NEXT_SESSION_KEY] == "/admin/"


@pytest.mark.django_db
@override_settings(**ENTRA_OPTIONAL)
def test_entra_id_login_ignores_external_next(client):
    with patch(
        "project.npda.views.entra_id.build_entra_id_client",
        return_value=FakeEntraClient(),
    ):
        client.get(reverse("entra_id_login"), {"next": "https://evil.example.com/"})

    assert ENTRA_ID_NEXT_SESSION_KEY not in client.session


# Completing the sign in


@pytest.mark.django_db
@override_settings(**ENTRA_REQUIRED)
@pytest.mark.parametrize("user_fixture", ["superuser", "audit_team_member"])
def test_entra_id_sign_in_logs_in_and_verifies_rcpch_staff(
    client, request, user_fixture
):
    user = request.getfixturevalue(user_fixture)
    fake = FakeEntraClient(result=claims_for(user.email.upper()))

    response = complete_entra_sign_in(client, fake, next_url="/admin/")

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == "/admin/"
    assert fake.redeemed_with == (
        {"state": "abc"},
        {"code": "the-code", "state": "abc"},
    )
    assert int(client.session["_auth_user_id"]) == user.pk
    assert ENTRA_ID_FLOW_SESSION_KEY not in client.session

    device = EntraIDDevice.objects.get(user=user)
    assert device.entra_object_id == OBJECT_ID
    assert device.last_used_at is not None
    assert client.session[DEVICE_ID_SESSION_KEY] == device.persistent_id

    assert VisitActivity.objects.filter(
        npdauser=user, activity=VisitActivity.SUCCESSFUL_LOGIN
    ).exists()

    # The session counts as 2FA verified and is not ended by the middleware
    response = client.get(reverse("home"))
    assert response.status_code == HTTPStatus.OK
    assert response.wsgi_request.user.is_verified()
    assert int(client.session["_auth_user_id"]) == user.pk


@pytest.mark.django_db
@override_settings(**ENTRA_OPTIONAL)
def test_entra_id_sign_in_goes_to_home_page_without_next(client, superuser):
    response = complete_entra_sign_in(
        client, FakeEntraClient(claims_for(superuser.email))
    )

    assert response.status_code == HTTPStatus.FOUND
    assert response.url.startswith("/period/")
    assert int(client.session["_auth_user_id"]) == superuser.pk


@pytest.mark.django_db
@override_settings(**ENTRA_REQUIRED)
def test_entra_id_sign_in_reuses_bound_device(client, superuser):
    EntraIDDevice.objects.create(
        user=superuser, name="Entra ID", entra_object_id=OBJECT_ID
    )

    complete_entra_sign_in(client, FakeEntraClient(claims_for(superuser.email)))

    assert int(client.session["_auth_user_id"]) == superuser.pk
    assert EntraIDDevice.objects.filter(user=superuser).count() == 1


def assert_refused(client, response, user=None, details_contains=None):
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse("two_factor:login")
    assert "_auth_user_id" not in client.session
    if user is not None:
        failure = VisitActivity.objects.get(
            npdauser=user, activity=VisitActivity.ENTRA_ID_LOGIN_FAILED
        )
        if details_contains:
            assert details_contains in failure.details


@pytest.mark.django_db
@override_settings(**ENTRA_REQUIRED)
def test_entra_id_sign_in_refused_for_clinicians(client, clinician):
    response = complete_entra_sign_in(
        client, FakeEntraClient(claims_for(clinician.email))
    )

    assert_refused(client, response, clinician, "not a superuser")
    assert not EntraIDDevice.objects.filter(user=clinician).exists()


@pytest.mark.django_db
@override_settings(**ENTRA_REQUIRED)
def test_entra_id_sign_in_refused_for_other_tenant(client, superuser):
    response = complete_entra_sign_in(
        client, FakeEntraClient(claims_for(superuser.email, tid="another-tenant"))
    )

    assert_refused(client, response)
    assert not EntraIDDevice.objects.filter(user=superuser).exists()


@pytest.mark.django_db
@override_settings(**ENTRA_REQUIRED)
def test_entra_id_sign_in_refused_for_unknown_email(client, superuser):
    response = complete_entra_sign_in(
        client, FakeEntraClient(claims_for("nobody@rcpch.ac.uk"))
    )

    assert_refused(client, response)


@pytest.mark.django_db
@override_settings(**ENTRA_REQUIRED)
def test_entra_id_sign_in_refused_for_inactive_user(client, superuser):
    superuser.is_active = False
    superuser.save()

    response = complete_entra_sign_in(
        client, FakeEntraClient(claims_for(superuser.email))
    )

    assert_refused(client, response, superuser, "inactive")


@pytest.mark.django_db
@override_settings(**ENTRA_REQUIRED)
def test_entra_id_sign_in_refused_when_microsoft_account_changes(client, superuser):
    EntraIDDevice.objects.create(
        user=superuser, name="Entra ID", entra_object_id="a-different-object-id"
    )

    response = complete_entra_sign_in(
        client, FakeEntraClient(claims_for(superuser.email))
    )

    assert_refused(client, response, superuser, "does not match")


@pytest.mark.django_db
@override_settings(**ENTRA_REQUIRED)
def test_entra_id_sign_in_refused_when_microsoft_returns_error(client, superuser):
    response = complete_entra_sign_in(
        client,
        FakeEntraClient(
            {"error": "access_denied", "error_description": "User cancelled"}
        ),
    )

    assert_refused(client, response)


@pytest.mark.django_db
@override_settings(**ENTRA_REQUIRED)
def test_entra_id_sign_in_refused_when_state_does_not_match(client, superuser):
    response = complete_entra_sign_in(
        client, FakeEntraClient(raises=ValueError("state mismatch"))
    )

    assert_refused(client, response)


@pytest.mark.django_db
@override_settings(**ENTRA_REQUIRED)
def test_entra_id_callback_refused_without_sign_in_in_progress(client, superuser):
    fake = FakeEntraClient(claims_for(superuser.email))
    with patch("project.npda.views.entra_id.build_entra_id_client", return_value=fake):
        response = client.get(reverse("entra_id_callback"), {"code": "x"})

    assert_refused(client, response)
    assert fake.redeemed_with is None


# Sessions started with a password (EntraIDLoginRequiredMiddleware)


def password_session(client, user):
    client.force_login(user)
    twofactor_signin(client, user)


@pytest.mark.django_db
@override_settings(LOCAL_DEV_BYPASS_2FA_AND_CAPTCHA=False, **ENTRA_REQUIRED)
def test_password_session_of_rcpch_staff_ended_when_required(client, superuser):
    password_session(client, superuser)

    response = client.get(reverse("home"))

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse("two_factor:login")
    assert "_auth_user_id" not in client.session
    # Their credentials are not touched
    assert TOTPDevice.objects.filter(user=superuser, name="default").exists()
    assert NPDAUser.objects.get(pk=superuser.pk).check_password(PASSWORD)


@pytest.mark.django_db
@override_settings(**ENTRA_REQUIRED)
def test_password_session_of_rcpch_staff_ended_with_htmx_redirect(client, superuser):
    password_session(client, superuser)

    response = client.get(reverse("home"), headers={"HX-Request": "true"})

    assert response["HX-Redirect"] == reverse("two_factor:login")
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
@override_settings(**ENTRA_REQUIRED)
def test_password_session_of_rcpch_staff_can_go_straight_to_entra_id(client, superuser):
    password_session(client, superuser)

    with patch(
        "project.npda.views.entra_id.build_entra_id_client",
        return_value=FakeEntraClient(),
    ):
        response = client.get(reverse("entra_id_login"))

    assert response.status_code == HTTPStatus.FOUND
    assert response.url.startswith("https://login.microsoftonline.com/")
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
@override_settings(LOCAL_DEV_BYPASS_2FA_AND_CAPTCHA=False, **ENTRA_OPTIONAL)
def test_password_session_of_rcpch_staff_kept_when_not_required(client, superuser):
    password_session(client, superuser)

    response = client.get(reverse("home"))

    assert response.status_code == HTTPStatus.OK
    assert int(client.session["_auth_user_id"]) == superuser.pk


@pytest.mark.django_db
@override_settings(LOCAL_DEV_BYPASS_2FA_AND_CAPTCHA=False, **ENTRA_REQUIRED)
def test_password_session_of_clinician_kept_when_required(client, clinician):
    password_session(client, clinician)

    response = client.get(reverse("home"))

    assert response.status_code == HTTPStatus.OK
    assert int(client.session["_auth_user_id"]) == clinician.pk


# Switching the setting off again


@pytest.mark.django_db
def test_switching_setting_off_restores_password_login(client, superuser):
    TOTPDevice.objects.create(user=superuser, name="default")

    with override_settings(**ENTRA_REQUIRED):
        with pytest.raises(ValidationError):
            CaptchaAuthenticationForm(request=None).confirm_login_allowed(superuser)

    with override_settings(**ENTRA_OPTIONAL):
        CaptchaAuthenticationForm(request=None).confirm_login_allowed(superuser)

    superuser.refresh_from_db()
    assert superuser.check_password(PASSWORD)
    assert TOTPDevice.objects.filter(user=superuser, name="default").exists()
