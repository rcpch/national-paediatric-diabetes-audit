"""Test the setup of the test database.

Seeds the test database with test data and checks that the data has been seeded.
"""

import pytest
import logging

from django.contrib.auth.models import Group

from project.npda.models import NPDAUser, OrganisationEmployer
from project.npda.models.paediatric_diabetes_unit import PaediatricDiabetesUnit
from project.npda.tests.factories.npda_user_factory import NPDAUserFactory
from project.npda.tests.UserDataClasses import (
    test_user_audit_centre_reader_data,
)
from project.constants import VIEW_PREFERENCES

# logging
logger = logging.getLogger(__name__)


@pytest.mark.django_db
def test__seed_test_db(
    seed_groups_fixture,
    seed_users_fixture,
    seed_patients_fixture,
):
    assert Group.objects.all().exists()
    assert OrganisationEmployer.objects.all().exists()
    assert NPDAUser.objects.all().exists()


@pytest.mark.django_db
def test__multiple_PaediatricsDiabetesUnitFactory_instances_not_created(
    seed_groups_fixture,
    seed_users_fixture,
    seed_patients_fixture,
):
    # GOSH User
    user_data = test_user_audit_centre_reader_data
    GOSH_PZ_CODE = "PZ196"

    for _ in range(5):
        new_user_gosh = NPDAUserFactory(
            first_name="test",
            role=user_data.role,
            # Assign flags based on user role
            is_active=user_data.is_active,
            is_staff=user_data.is_staff,
            is_rcpch_audit_team_member=user_data.is_rcpch_audit_team_member,
            is_rcpch_staff=user_data.is_rcpch_staff,
            groups=[user_data.group_name],
            view_preference=(VIEW_PREFERENCES[0][0]),
            organisation_employers=[GOSH_PZ_CODE],
        )

        assert PaediatricDiabetesUnit.objects.filter(pz_code=GOSH_PZ_CODE).count() == 1
