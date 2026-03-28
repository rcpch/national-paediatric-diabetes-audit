"""
Seeds NPDA Users in test db once per session.
"""

import logging

# Standard imports
import pytest

from project.npda.models import NPDAUser
from project.npda.tests.factories.npda_user_factory import NPDAUserFactory

# NPDA Imports
from project.npda.tests.UserDataClasses import (
    test_user_audit_centre_coordinator_data,
    test_user_audit_centre_editor_data,
    test_user_audit_centre_reader_data,
    test_user_rcpch_audit_team_data,
)

logger = logging.getLogger(__name__)


def _seed_users_fixture(django_db_setup, django_db_blocker, test_pz_codes_fixture):

    # Define user data to seed
    users = [
        test_user_audit_centre_reader_data,
        test_user_audit_centre_editor_data,
        test_user_audit_centre_coordinator_data,
        test_user_rcpch_audit_team_data,
    ]

    with django_db_blocker.unblock():

        if NPDAUser.objects.exists():
            logger.info("NOTE: Test users already seeded! Not re-seeding.")
            return

        logger.info(f"Seeding test users at {', '.join(test_pz_codes_fixture)}.")

        for pz_code in test_pz_codes_fixture:
            # Seed a user of each type
            for user in users:
                first_name = user.role_str
                new_user = NPDAUserFactory(
                    first_name=first_name,
                    role=user.role,
                    is_active=True,
                    is_staff=False,
                    is_rcpch_audit_team_member=user.is_rcpch_audit_team_member,
                    is_rcpch_staff=user.is_rcpch_staff,
                    groups=[user.group_name],
                    organisation_employers=[pz_code],
                )

        assert NPDAUser.objects.count() == len(users) * len(test_pz_codes_fixture)


@pytest.fixture(scope="session")
def seed_users_fixture(django_db_setup, django_db_blocker, test_pz_codes_fixture):
    _seed_users_fixture(django_db_setup, django_db_blocker, test_pz_codes_fixture)


# Required if multiple tests use transactional_db
@pytest.fixture(scope="function")
def seed_users_per_function_fixture(
    django_db_setup, django_db_blocker, test_pz_codes_function_fixture
):
    _seed_users_fixture(
        django_db_setup, django_db_blocker, test_pz_codes_function_fixture
    )
