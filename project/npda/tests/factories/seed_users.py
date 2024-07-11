"""
Seeds NPDA Users in test db once per session.
"""

# Standard imports
from project.npda.general_functions.rcpch_nhs_organisations import get_nhs_organisation
import pytest


# NPDA Imports
from project.npda.tests.UserDataClasses import (
    test_user_audit_centre_coordinator_data,
    test_user_audit_centre_editor_data,
    test_user_audit_centre_reader_data,
    test_user_rcpch_audit_team_data,
)
from project.npda.models import (
    NPDAUser,
    OrganisationEmployer,
)
from .NPDAUserFactory import NPDAUserFactory
from project.constants.user import RCPCH_AUDIT_TEAM
from project.constants import VIEW_PREFERENCES
import logging

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def seed_users_fixture(django_db_setup, django_db_blocker):

    # Define user data to seed
    users = [
        test_user_audit_centre_reader_data,
        test_user_audit_centre_editor_data,
        test_user_audit_centre_coordinator_data,
        test_user_rcpch_audit_team_data,
    ]

    with django_db_blocker.unblock():

        # Don't repeat seed if users already exist.
        if NPDAUser.objects.exists():
            logger.info("Test users already seeded. Skipping")
            return

        # Otherwise, seed the users
        is_active = True
        is_staff = False
        is_rcpch_audit_team_member = False
        is_rcpch_staff = False

        GOSH_ODS_CODE = "RP401"
        ALDER_HEY_ODS_CODE = "RBS25"

        logger.info(f"Seeding test users at {GOSH_ODS_CODE=}.")
        # Seed a user of each type at GOSH
        for user in users:
            first_name = user.role_str

            if user.role == RCPCH_AUDIT_TEAM:
                is_rcpch_audit_team_member = True
                is_rcpch_staff = True

            if user.is_clinical_audit_team:
                is_rcpch_audit_team_member = True

            # GOSH User
            new_user_gosh = NPDAUserFactory(
                first_name=first_name,
                role=user.role,
                # Assign flags based on user role
                is_active=is_active,
                is_staff=is_staff,
                is_rcpch_audit_team_member=is_rcpch_audit_team_member,
                is_rcpch_staff=is_rcpch_staff,
                groups=[user.group_name],
                organisation_employers=[
                    GOSH_ODS_CODE
                ],  # Factory handles creating and assigning OrganisationEmployer
                view_preference=(
                    VIEW_PREFERENCES[2][0]
                    if user.role == RCPCH_AUDIT_TEAM
                    else VIEW_PREFERENCES[0][0]
                ),
            )

            # Alder hey user
            new_user_alder_hey = NPDAUserFactory(
                first_name=first_name,
                role=user.role,
                # Assign flags based on user role
                is_active=is_active,
                is_staff=is_staff,
                is_rcpch_audit_team_member=is_rcpch_audit_team_member,
                is_rcpch_staff=is_rcpch_staff,
                groups=[user.group_name],
                organisation_employers=[
                    ALDER_HEY_ODS_CODE
                ],  # Factory handles creating and assigning OrganisationEmployer
            )

            logger.info(f"Seeded {new_user_gosh=} and {new_user_alder_hey=}")
        logger.info(f"All test users sucessfully seeded: {NPDAUser.objects.all()=}")
