"""
This file houses code to be copied and pasted easily into the Django Python shell.
"""

# Seeds test db users according to role + permissions.

from django.contrib.auth.models import Group
from npda.tests.UserDataClasses import (
    test_user_audit_centre_reader_data,
    test_user_audit_centre_editor_data,
    test_user_audit_centre_coordinator_data,
    test_user_rcpch_audit_team_data,
    test_user_clinicial_audit_team_data,
)

from npda.models import Organisation
from project.npda.tests.factories.NPDAUserFactory import NPDAUserFactory
from project.constants.user import RCPCH_AUDIT_TEAM

users = [
    test_user_audit_centre_reader_data,
    test_user_audit_centre_editor_data,
    test_user_audit_centre_coordinator_data,
    test_user_rcpch_audit_team_data,
    test_user_clinicial_audit_team_data,
]

TEST_USER_ORGANISATION = Organisation.objects.get(
    ods_code="RP401",
    trust__ods_code="RP4",
)

NPDAUserFactory(
    first_name=test_user_audit_centre_reader_data.role_str,
    role=test_user_audit_centre_reader_data.role,
    # Assign flags based on user role
    is_active=True,
    is_staff=False,
    is_rcpch_audit_team_member=False,
    is_rcpch_staff=False,
    organisation_employer=TEST_USER_ORGANISATION,
    groups=[test_user_audit_centre_reader_data.group_name],
)
NPDAUserFactory(
    first_name=test_user_audit_centre_editor_data.role_str,
    role=test_user_audit_centre_editor_data.role,
    # Assign flags based on user role
    is_active=True,
    is_staff=False,
    is_rcpch_audit_team_member=False,
    is_rcpch_staff=False,
    organisation_employer=TEST_USER_ORGANISATION,
    groups=[test_user_audit_centre_editor_data.group_name],
)

NPDAUserFactory(
    first_name=test_user_rcpch_audit_team_data.role_str,
    role=test_user_rcpch_audit_team_data.role,
    # Assign flags based on user role
    is_active=True,
    is_staff=False,
    is_rcpch_audit_team_member=False,
    is_rcpch_staff=False,
    organisation_employer=TEST_USER_ORGANISATION,
    groups=[test_user_rcpch_audit_team_data.group_name],
)

# Welsh Coordinator
NPDAUserFactory(
    first_name=test_user_audit_centre_coordinator_data.role_str,
    role=test_user_audit_centre_coordinator_data.role,
    surname="WELSH",
    is_active=False,
    is_staff=False,
    is_rcpch_audit_team_member=False,
    is_rcpch_staff=False,
    organisation_employer=Organisation.objects.get(pk=333),
    groups=[test_user_audit_centre_coordinator_data.group_name],
)
