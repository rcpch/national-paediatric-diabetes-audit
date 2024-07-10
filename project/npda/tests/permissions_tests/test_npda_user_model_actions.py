"""Tests for NPDAUser model actions."""

# Python imports
import pytest
import logging
from http import HTTPStatus

# 3rd party imports
from django.urls import reverse
from django.test import Client

# E12 imports
from project.npda.models import NPDAUser
from project.npda.tests.utils import set_session_attributes_for_signedin_user
from project.npda.tests.UserDataClasses import test_user_rcpch_audit_team_data
from project.npda.views.npda_users import NPDAUserListView


logger = logging.getLogger(__name__)


def login_test_user(client: Client, user, password: str = "pw"):
    """
    Helper function to log in a test user using the custom RCPCHLoginView.
    """
    login_url = reverse(
        "two_factor:login"
    )  # Adjust the URL name based on your configuration

    # Simulate login POST request
    response = client.post(
        login_url,
        {
            "auth-username": user.email,
            "auth-password": password,
            "auth-remember": "on",
        },
    )

    # Check if login was successful
    assert response.status_code == 302  # Redirect after successful login

    # The user should now be logged in and session data should be set
    session = client.session
    current_user_ods_code = user.organisation_employers.first().ods_code
    current_user_pz_code = user.organisation_employers.first().pz_code

    assert session["ods_code"] == current_user_ods_code
    assert session["pz_code"] == current_user_pz_code
    assert "sibling_organisations" in session
    assert "organisation_choices" in session
    assert "pdu_choices" in session

    return client


@pytest.mark.django_db
def test_users_cannot_view_user_table_from_different_pdus(
    seed_groups_fixture,
    seed_users_fixture,
    seed_patients_fixture,
    client,
):
    """Except for RCPCH_AUDIT_TEAM, users cannot view the user table from different PDUs."""

    ALDER_HEY_PZ_CODE = "PZ074"
    ALDER_HEY_ODS_CODE = "RBS25"

    # Get users which cannot view the user table from different PDUs.
    test_users_ah = NPDAUser.objects.exclude(
        first_name=test_user_rcpch_audit_team_data.role_str,
    ).filter(organisation_employers__pz_code=ALDER_HEY_PZ_CODE)

    test_user_count = test_users_ah.count()

    # Check we have the correct number.
    expected_test_user_count_excluding_rcpch_audit_team = 3
    assert (
        test_user_count == expected_test_user_count_excluding_rcpch_audit_team
    ), f"Expected {expected_test_user_count_excluding_rcpch_audit_team} test users, got {test_user_count=}"

    # For each user, ensure the queryset does not contain users from a PDU they are not part of Alder Hey (other seeded users are at GOSH).
    for test_user in test_users_ah:

        client = set_session_attributes_for_signedin_user(
            client=client, user=test_user, ods_code=ALDER_HEY_ODS_CODE
        )

        # Simulate a GET request to the NPDAUserListView
        url = reverse("npda_users")  
        response = client.get(url)

        # Check that the response is successful
        assert response.status_code in [HTTPStatus.OK, HTTPStatus.FOUND]

        # Extract the queryset from the context
        view = NPDAUserListView()
        view.request = response.wsgi_request
        view.request.user = test_user  # Explicitly set the user in the request
        queryset = view.get_queryset()

        # Ensure the queryset does not contain users from a PDU they are not part of
        assert (
            queryset.exclude(organisation_employers__pz_code=ALDER_HEY_PZ_CODE).count()
            == 0
        ), f"User {test_user} from {ALDER_HEY_PZ_CODE=} can see NPDAUsers from other PDUs."


@pytest.mark.django_db
def test_rcpch_audit_team_can_view_all_npdausers(
    seed_groups_fixture,
    seed_users_fixture,
    seed_patients_fixture,
    client,
):
    """RCPCH_AUDIT_TEAM users can view all users."""

    # Get an RCPCH_AUDIT_TEAM user
    test_user_rcpch_audit_team = NPDAUser.objects.filter(
        first_name=test_user_rcpch_audit_team_data.role_str
    ).first()

    # Get all users
    all_users = NPDAUser.objects.all()
    all_user_count = all_users.count()

    # Set the session for the RCPCH_AUDIT_TEAM user
    client = set_session_attributes_for_signedin_user(
        client=client, user=test_user_rcpch_audit_team, ods_code="RP401"
    )

    # Simulate a GET request to the NPDAUserListView
    url = reverse("npda_users")  
    response = client.get(url)

    # Check that the response is successful
    assert response.status_code in [HTTPStatus.OK, HTTPStatus.FOUND]

    # Extract the queryset from the context
    view = NPDAUserListView()
    view.request = response.wsgi_request
    view.request.user = test_user_rcpch_audit_team  # Explicitly set the user in the request
    queryset = view.get_queryset()
    
    for user in NPDAUser.objects.all():
        print(f'{user.first_name} -> {user.view_preference=}')

    # Ensure the queryset contains all users
    assert (
        queryset.count() == all_user_count
    ), f"RCPCH_AUDIT_TEAM user cannot see all users. Expected {all_user_count}, got {queryset.count()}."
