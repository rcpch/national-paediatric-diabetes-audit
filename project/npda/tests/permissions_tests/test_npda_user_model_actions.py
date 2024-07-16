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
from project.npda.tests.utils import login_and_verify_user
from project.npda.tests.UserDataClasses import test_user_rcpch_audit_team_data
from project.npda.views.npda_users import NPDAUserListView
from project.constants.user import RCPCH_AUDIT_TEAM

logger = logging.getLogger(__name__)

ALDER_HEY_PZ_CODE = "PZ074"
ALDER_HEY_ODS_CODE = "RBS25"


@pytest.mark.django_db
def test_npda_user_list_view_users_can_only_see_users_from_their_pdu(
    seed_groups_fixture,
    seed_users_fixture,
    seed_patients_fixture,
    client,
):
    """Except for RCPCH_AUDIT_TEAM, users should only see users from their own PDU."""

    ah_users = NPDAUser.objects.filter(organisation_employers__pz_code=ALDER_HEY_PZ_CODE)
    # Check there are users from outside Alder Hey so this test doesn't pass by accident
    non_ah_users = NPDAUser.objects.exclude(organisation_employers__pz_code=ALDER_HEY_PZ_CODE)
    assert(non_ah_users.count() > 0)

    ah_user = ah_users.first()

    client = login_and_verify_user(client, ah_user)

    url = reverse("npda_users")
    response = client.get(url)

    assert response.status_code == HTTPStatus.OK

    users = response.context_data['object_list']

    for user in users:
        pz_codes = [org['pz_code'] for org in user.organisation_employers.values()]

        if not ALDER_HEY_PZ_CODE in pz_codes:
            pytest.fail(f"{ah_user} in {ALDER_HEY_PZ_CODE} should not be able to see {user} in {pz_codes}")


@pytest.mark.django_db
def test_npda_user_list_view_rcpch_audit_team_can_view_all_users(
    seed_groups_fixture,
    seed_users_fixture,
    seed_patients_fixture,
    client,
):
    """RCPCH_AUDIT_TEAM users can view all users."""

    ah_users = NPDAUser.objects.filter(organisation_employers__pz_code=ALDER_HEY_PZ_CODE)
    # Check there are users from outside Alder Hey so this test doesn't pass by accident
    non_ah_users = NPDAUser.objects.exclude(organisation_employers__pz_code=ALDER_HEY_PZ_CODE)
    assert(non_ah_users.count() > 0)

    ah_audit_team_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=RCPCH_AUDIT_TEAM
    ).first()

    client = login_and_verify_user(client, ah_audit_team_user)

    url = reverse("npda_users")

    # The user still defaults to seeing users from just their PDU
    # This is the request made when you click the "All" button on the switcher in the UI
    set_view_preference_response = client.post(url, {
        "view_preference": 2
    })

    assert set_view_preference_response.status_code == HTTPStatus.OK

    response = client.get(url)

    assert response.status_code == HTTPStatus.OK

    users = response.context_data['object_list']
    print(f"!! {users}")
    
    assert(users.count() > ah_users.count())
