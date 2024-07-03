"""
Set up dataclasses for E12 User Test Fixtures
"""

# Standard Imports
from dataclasses import dataclass
from project.npda.general_functions import group_for_role

# RCPCH Imports
from project.constants.user import (
    AUDIT_CENTRE_READER,
    AUDIT_CENTRE_EDITOR,
    AUDIT_CENTRE_COORDINATOR,
    RCPCH_AUDIT_TEAM,
    TRUST_AUDIT_TEAM_VIEW_ONLY,
    TRUST_AUDIT_TEAM_EDIT_ACCESS,
    TRUST_AUDIT_TEAM_COORDINATOR_ACCESS,
    NPDA_AUDIT_TEAM_FULL_ACCESS,
)


@dataclass
class TestUser:
    role: int
    role_str: str
    is_clinical_audit_team: bool = False
    is_active: bool = False
    is_staff: bool = False
    is_rcpch_audit_team_member: bool = False
    is_rcpch_staff: bool = False

    @property
    def group_name(self):
        return group_for_role(self.role)


test_user_audit_centre_reader_data = TestUser(
    role=AUDIT_CENTRE_READER,
    is_active=True,
    is_staff=False,
    role_str="AUDIT_CENTRE_READER",
    is_rcpch_audit_team_member=False,
    is_rcpch_staff=False,
)

test_user_audit_centre_editor_data = TestUser(
    role=AUDIT_CENTRE_EDITOR,
    role_str="AUDIT_CENTRE_EDITOR",
    is_active=True,
    is_staff=False,
    is_rcpch_audit_team_member=False,
    is_rcpch_staff=False,
)

test_user_audit_centre_coordinator_data = TestUser(
    role=AUDIT_CENTRE_COORDINATOR,
    role_str="AUDIT_CENTRE_COORDINATOR",
    is_active=True,
    is_staff=False,
    is_rcpch_audit_team_member=False,
    is_rcpch_staff=False,
)

test_user_rcpch_audit_team_data = TestUser(
    role=RCPCH_AUDIT_TEAM,
    role_str="RCPCH_AUDIT_TEAM",
    is_active=True,
    is_staff=False,
    is_rcpch_audit_team_member=True,
    is_rcpch_staff=True,
)
