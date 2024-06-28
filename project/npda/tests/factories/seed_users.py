"""
Seeds NPDA Users in test db once per session.
"""

# Standard imports
import pytest

# 3rd Party imports
from django.contrib.auth.models import Group

# NPDA Imports
from project.npda.tests.UserDataClasses import (
    test_user_audit_centre_coordinator_data,
    test_user_audit_centre_editor_data,
    test_user_audit_centre_reader_data,
    test_user_rcpch_audit_team_data,
)
from project.npda.models import (
    NPDAUser,
    # Organisation,
)
from .NPDAUserFactory import NPDAUserFactory
from project.constants.user import (
    RCPCH_AUDIT_TEAM,
)


@pytest.mark.django_db
@pytest.fixture(scope="session")
def seed_users_fixture(django_db_setup, django_db_blocker):
    users = [
        test_user_audit_centre_reader_data,
        test_user_audit_centre_editor_data,
        test_user_audit_centre_coordinator_data,
        test_user_rcpch_audit_team_data,
    ]

    with django_db_blocker.unblock():
        # Don't repeat seed
        if not NPDAUser.objects.exists():
            # TEST_USER_ORGANISATION = Organisation.objects.get(
            #     ods_code="RP401",
            #     trust__ods_code="RP4",
            # )

            is_active = True
            is_staff = False
            is_rcpch_audit_team_member = False
            is_rcpch_staff = False

            # seed a user of each type at GOSH
            for user in users:
                first_name = user.role_str

                # set RCPCH AUDIT TEAM MEMBER ATTRIBUTE
                if user.role == RCPCH_AUDIT_TEAM:
                    is_rcpch_audit_team_member = True
                    is_rcpch_staff = True

                if user.is_clinical_audit_team:
                    is_rcpch_audit_team_member = True
                    first_name = "CLINICAL_AUDIT_TEAM"

                NPDAUserFactory(
                    first_name=first_name,
                    role=user.role,
                    # Assign flags based on user role
                    is_active=is_active,
                    is_staff=is_staff,
                    is_rcpch_audit_team_member=is_rcpch_audit_team_member,
                    is_rcpch_staff=is_rcpch_staff,
                    # organisation_employer=TEST_USER_ORGANISATION,
                    groups=[user.group_name],
                )
        else:
            print("Test users already seeded. Skipping")
