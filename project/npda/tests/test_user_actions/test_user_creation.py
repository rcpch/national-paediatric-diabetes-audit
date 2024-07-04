"""Tests for creating users."""

# python imports
import pytest
import logging
from http import HTTPStatus

# 3rd party imports
from django.urls import reverse
from project.constants.user import TITLES

# E12 imports
from project.npda.models import NPDAUser, OrganisationEmployer
from project.npda.tests.utils import set_session_attributes_for_user

logger = logging.getLogger(__name__)


@pytest.mark.django_db
def test_user_creation(
    seed_groups_fixture,
    seed_users_fixture,
    seed_patients_fixture,
    client,
):
    """Test user can create in same organisation"""

    test_users = NPDAUser.objects.all()

    # For each test user, create a user in the same organisation
    for test_user in test_users:

        data = {
            "title": TITLES[0][0],  # Mr
            "first_name": "Test",
            "surname": "User",
            "email": "test@test.com",
            # "organisation_employers": test_user.organisation_employers.first(),
        }

        # Login and OTP ENABLE
        client = set_session_attributes_for_user(client=client, user=test_user)

        url = reverse("npdauser-create")

        # Try creating a user
        response = client.post(url, data)

        logger.info(f"Response: {response}")

        logger.info(NPDAUser.objects.all())