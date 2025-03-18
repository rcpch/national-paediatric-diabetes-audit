"""Tests that ensure that views load under normal conditions"""

from django.urls import reverse
import pytest

from django.test import Client

from project.npda.models.npda_user import NPDAUser
from project.npda.tests.factories.npda_user_factory import NPDAUserFactory
from project.npda.tests.permissions_tests.test_npda_user_model_actions import ALDER_HEY_PZ_CODE
from project.npda.tests.utils import login_and_verify_user


@pytest.mark.django_db
def test_pt_level_report_loads(seed_groups_fixture, seed_users_fixture, client: Client):
    ah_users = NPDAUser.objects.filter(organisation_employers__pz_code=ALDER_HEY_PZ_CODE)

    ah_user = ah_users.first()

    client = login_and_verify_user(client, ah_user)

    url = reverse("npda_users")
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_dashboard_loads(seed_groups_fixture, seed_users_fixture, client: Client):
    ah_users = NPDAUser.objects.filter(organisation_employers__pz_code=ALDER_HEY_PZ_CODE)

    ah_user = ah_users.first()

    client = login_and_verify_user(client, ah_user)

    url = reverse("dashboard")
    response = client.get(url)
    assert response.status_code == 200
