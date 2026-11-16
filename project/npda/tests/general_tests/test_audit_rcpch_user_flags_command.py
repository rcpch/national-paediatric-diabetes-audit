"""
Tests for the ``audit_rcpch_user_flags`` management command.

The command is a read-only report of users whose RCPCH flags, role and groups
disagree. The test database may already contain seeded users, so each test
checks only for the users it creates.
"""

import csv
from io import StringIO

import pytest
from django.contrib.auth.models import Group
from django.core.management import call_command

from project.constants import (
    AUDIT_CENTRE_COORDINATOR,
    NPDA_AUDIT_TEAM_FULL_ACCESS,
    RCPCH_AUDIT_TEAM,
    TRUST_AUDIT_TEAM_COORDINATOR_ACCESS,
    TRUST_AUDIT_TEAM_VIEW_ONLY,
)
from project.npda.management.commands.audit_rcpch_user_flags import (
    FLAG_WITHOUT_ROLE,
    GROUP_MISMATCH,
    ROLE_WITHOUT_FLAG,
    STAFF_FLAG_ONLY,
)
from project.npda.tests.factories.npda_user_factory import NPDAUserFactory


def _csv_rows_by_email(*args):
    out = StringIO()
    call_command("audit_rcpch_user_flags", "--csv", *args, stdout=out)
    return {row["email"]: row for row in csv.DictReader(StringIO(out.getvalue()))}


def _findings(row):
    return set(row["findings"].split(";"))


def _group(name):
    return Group.objects.get(name=name)


@pytest.mark.django_db
def test_consistent_audit_team_user_is_not_reported(seed_groups_fixture):
    user = NPDAUserFactory(
        role=RCPCH_AUDIT_TEAM,
        is_rcpch_audit_team_member=True,
        is_rcpch_staff=True,
        groups=[_group(NPDA_AUDIT_TEAM_FULL_ACCESS)],
    )

    assert user.email not in _csv_rows_by_email()


@pytest.mark.django_db
def test_consistent_coordinator_is_not_reported(seed_groups_fixture):
    user = NPDAUserFactory(
        role=AUDIT_CENTRE_COORDINATOR,
        groups=[_group(TRUST_AUDIT_TEAM_COORDINATOR_ACCESS)],
    )

    assert user.email not in _csv_rows_by_email()


@pytest.mark.django_db
def test_coordinator_with_audit_team_flag_is_reported(seed_groups_fixture):
    """The main risk: a PDU user with the flag loses national access."""
    user = NPDAUserFactory(
        role=AUDIT_CENTRE_COORDINATOR,
        is_rcpch_audit_team_member=True,
        groups=[_group(TRUST_AUDIT_TEAM_COORDINATOR_ACCESS)],
    )

    row = _csv_rows_by_email()[user.email]
    assert _findings(row) == {FLAG_WITHOUT_ROLE}
    assert row["expected_group"] == TRUST_AUDIT_TEAM_COORDINATOR_ACCESS


@pytest.mark.django_db
def test_staff_flag_alone_is_reported(seed_groups_fixture):
    user = NPDAUserFactory(
        role=AUDIT_CENTRE_COORDINATOR,
        is_rcpch_staff=True,
        groups=[_group(TRUST_AUDIT_TEAM_COORDINATOR_ACCESS)],
    )

    assert _findings(_csv_rows_by_email()[user.email]) == {
        FLAG_WITHOUT_ROLE,
        STAFF_FLAG_ONLY,
    }


@pytest.mark.django_db
def test_audit_team_role_without_staff_flag_is_reported(seed_groups_fixture):
    user = NPDAUserFactory(
        role=RCPCH_AUDIT_TEAM,
        is_rcpch_audit_team_member=True,
        is_rcpch_staff=False,
        groups=[_group(NPDA_AUDIT_TEAM_FULL_ACCESS)],
    )

    assert _findings(_csv_rows_by_email()[user.email]) == {ROLE_WITHOUT_FLAG}


@pytest.mark.django_db
def test_audit_team_role_with_only_staff_flag_is_reported(seed_groups_fixture):
    user = NPDAUserFactory(
        role=RCPCH_AUDIT_TEAM,
        is_rcpch_audit_team_member=False,
        is_rcpch_staff=True,
        groups=[_group(NPDA_AUDIT_TEAM_FULL_ACCESS)],
    )

    assert _findings(_csv_rows_by_email()[user.email]) == {
        STAFF_FLAG_ONLY,
        ROLE_WITHOUT_FLAG,
    }


@pytest.mark.django_db
def test_wrong_or_extra_groups_are_reported(seed_groups_fixture):
    wrong_group = NPDAUserFactory(
        role=RCPCH_AUDIT_TEAM,
        is_rcpch_audit_team_member=True,
        is_rcpch_staff=True,
        groups=[_group(TRUST_AUDIT_TEAM_VIEW_ONLY)],
    )
    extra_group = NPDAUserFactory(
        role=AUDIT_CENTRE_COORDINATOR,
        groups=[
            _group(TRUST_AUDIT_TEAM_COORDINATOR_ACCESS),
            _group(NPDA_AUDIT_TEAM_FULL_ACCESS),
        ],
    )
    no_group = NPDAUserFactory(role=AUDIT_CENTRE_COORDINATOR)

    rows = _csv_rows_by_email()
    for user in (wrong_group, extra_group, no_group):
        assert _findings(rows[user.email]) == {GROUP_MISMATCH}


@pytest.mark.django_db
def test_primary_pdu_is_reported(seed_groups_fixture):
    user = NPDAUserFactory(
        role=AUDIT_CENTRE_COORDINATOR,
        is_rcpch_audit_team_member=True,
        groups=[_group(TRUST_AUDIT_TEAM_COORDINATOR_ACCESS)],
        organisation_employers=["PZ130"],
    )

    assert _csv_rows_by_email()[user.email]["primary_pdu"] == "PZ130"


@pytest.mark.django_db
def test_active_only_skips_inactive_users(seed_groups_fixture):
    user = NPDAUserFactory(
        role=AUDIT_CENTRE_COORDINATOR,
        is_rcpch_audit_team_member=True,
        is_active=False,
        groups=[_group(TRUST_AUDIT_TEAM_COORDINATOR_ACCESS)],
    )

    assert user.email in _csv_rows_by_email()
    assert user.email not in _csv_rows_by_email("--active-only")


@pytest.mark.django_db
def test_text_report_and_no_writes(seed_groups_fixture):
    user = NPDAUserFactory(
        role=AUDIT_CENTRE_COORDINATOR,
        is_rcpch_audit_team_member=True,
        groups=[_group(TRUST_AUDIT_TEAM_COORDINATOR_ACCESS)],
    )
    updated_at = user.updated_at

    out = StringIO()
    call_command("audit_rcpch_user_flags", stdout=out)

    assert user.email in out.getvalue()
    assert "will LOSE national access" in out.getvalue()
    user.refresh_from_db()
    assert user.updated_at == updated_at
    assert user.is_rcpch_audit_team_member is True
    assert user.role == AUDIT_CENTRE_COORDINATOR


@pytest.mark.django_db
def test_csv_output_file(seed_groups_fixture, tmp_path):
    user = NPDAUserFactory(
        role=AUDIT_CENTRE_COORDINATOR,
        is_rcpch_audit_team_member=True,
        groups=[_group(TRUST_AUDIT_TEAM_COORDINATOR_ACCESS)],
    )
    output = tmp_path / "report.csv"

    call_command(
        "audit_rcpch_user_flags",
        "--csv",
        "--output",
        str(output),
        stdout=StringIO(),
        stderr=StringIO(),
    )

    with open(output, newline="") as handle:
        rows = {row["email"]: row for row in csv.DictReader(handle)}
    assert _findings(rows[user.email]) == {FLAG_WITHOUT_ROLE}
