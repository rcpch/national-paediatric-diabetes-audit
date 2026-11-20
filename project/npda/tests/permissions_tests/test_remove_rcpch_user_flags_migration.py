"""
Migration 0048 removes the retired is_rcpch_audit_team_member / is_rcpch_staff
fields from the model but keeps their columns, so the previous revision keeps
working while a deploy drains. It also records who held the flags.

The columns still exist in the test database, so the tests reach them through
the model as it was at 0047.
"""

import importlib

import pytest
from django.db import connection
from django.db.migrations.loader import MigrationLoader

from project.constants import AUDIT_CENTRE_COORDINATOR, RCPCH_AUDIT_TEAM
from project.npda.models import VisitActivity
from project.npda.tests.factories.npda_user_factory import NPDAUserFactory

migration = importlib.import_module(
    "project.npda.migrations.0048_remove_rcpch_user_flags_from_models"
)


def _apps_before_removal():
    loader = MigrationLoader(connection)
    return loader.project_state(("npda", "0047_rcpch_audit_team_permissions")).apps


@pytest.mark.django_db
def test_new_users_get_false_from_the_column_default(seed_groups_fixture):
    """Inserts that omit the columns still work, and old code reads False."""
    user = NPDAUserFactory(role=RCPCH_AUDIT_TEAM)

    OldNPDAUser = _apps_before_removal().get_model("npda", "NPDAUser")
    old_user = OldNPDAUser.objects.get(pk=user.pk)

    assert old_user.is_rcpch_audit_team_member is False
    assert old_user.is_rcpch_staff is False


@pytest.mark.django_db
def test_flags_are_recorded_in_visit_activity(seed_groups_fixture):
    both = NPDAUserFactory(role=RCPCH_AUDIT_TEAM)
    staff_only = NPDAUserFactory(role=AUDIT_CENTRE_COORDINATOR)
    neither = NPDAUserFactory(role=AUDIT_CENTRE_COORDINATOR)

    old_apps = _apps_before_removal()
    OldNPDAUser = old_apps.get_model("npda", "NPDAUser")
    OldNPDAUser.objects.filter(pk=both.pk).update(
        is_rcpch_audit_team_member=True, is_rcpch_staff=True
    )
    OldNPDAUser.objects.filter(pk=staff_only.pk).update(is_rcpch_staff=True)

    migration.record_flags_at_removal(old_apps, None)

    def recorded(user):
        return list(
            VisitActivity.objects.filter(
                npdauser=user,
                activity=13,
                details__startswith="RCPCH flags at removal",
            ).values_list("details", flat=True)
        )

    assert recorded(both) == [
        "RCPCH flags at removal: is_rcpch_audit_team_member=True, is_rcpch_staff=True"
    ]
    assert recorded(staff_only) == [
        "RCPCH flags at removal: is_rcpch_audit_team_member=False, is_rcpch_staff=True"
    ]
    assert recorded(neither) == []
