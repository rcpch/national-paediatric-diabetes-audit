"""Tests for the template download view"""

import logging
from http import HTTPStatus

# Python imports
import pytest
# 3rd party imports
from django.urls import reverse

from project.constants.csv_headings import (UNIQUE_IDENTIFIER_ENGLAND,
                                            UNIQUE_IDENTIFIER_JERSEY)
from project.constants.user import VIEW_PREFERENCES
# E12 imports
from project.npda.models import NPDAUser
from project.npda.tests.constants_for_tests import ALDER_HEY_PZ_CODE
from project.npda.tests.factories.npda_user_factory import NPDAUserFactory
from project.npda.tests.UserDataClasses import test_user_rcpch_audit_team_data
from project.npda.tests.utils import login_and_verify_user

logger = logging.getLogger(__name__)


@pytest.mark.django_db
def test_both_jersey_and_england_template_download_works(
    seed_groups_fixture,
    seed_users_fixture,
    client,
):
    """Test that the template download works for both Jersey and England and Wales"""

    user_england = NPDAUser.objects.filter(
        role=test_user_rcpch_audit_team_data.role,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()

    # Also create a Jersey user
    user_jersey = NPDAUserFactory(
        first_name="jersey_user",
        role=test_user_rcpch_audit_team_data.role,
        is_active=True,
        is_staff=False,
        is_rcpch_audit_team_member=test_user_rcpch_audit_team_data.is_rcpch_audit_team_member,
        is_rcpch_staff=test_user_rcpch_audit_team_data.is_rcpch_staff,
        groups=[test_user_rcpch_audit_team_data.group_name],
        view_preference=(VIEW_PREFERENCES[2][0]),
        organisation_employers=["PZ248"],
    )

    for user in [user_england, user_jersey]:
        login_and_verify_user(client, user)
        response = client.get(reverse("download_template"))
        assert response.status_code == HTTPStatus.OK

        if user.first_name == "jersey_user":
            UNIQUE_IDENTIFIER_HEADER = UNIQUE_IDENTIFIER_JERSEY[0]["heading"]
        else:
            UNIQUE_IDENTIFIER_HEADER = UNIQUE_IDENTIFIER_ENGLAND[0]["heading"]

        assert response.content.decode("utf-8").startswith(UNIQUE_IDENTIFIER_HEADER)
