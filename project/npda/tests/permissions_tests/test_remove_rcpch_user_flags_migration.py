"""
The retired is_rcpch_audit_team_member / is_rcpch_staff fields.

0048 recorded who held the flags in VisitActivity and removed the fields from
the model, keeping the columns while the previous revision drained. 0049 drops
the columns.
"""

import importlib
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from django.db import connection

FLAG_COLUMNS = {"is_rcpch_audit_team_member", "is_rcpch_staff"}

remove_from_models = importlib.import_module(
    "project.npda.migrations.0048_remove_rcpch_user_flags_from_models"
)


@pytest.mark.django_db
def test_flag_columns_are_dropped():
    with connection.cursor() as cursor:
        columns = {
            column.name
            for column in connection.introspection.get_table_description(
                cursor, "npda_npdauser"
            )
        }

    assert "role" in columns
    assert not FLAG_COLUMNS & columns


def test_flags_at_removal_are_recorded_per_flagged_user():
    """
    0048's snapshot writes one activity 13 entry per flagged user. The columns
    are gone, so this checks it against stand-in models.
    """
    NPDAUser = MagicMock()
    NPDAUser.objects.filter.return_value.values_list.return_value = [
        (1, True, True),
        (2, False, True),
    ]
    VisitActivity = MagicMock(side_effect=lambda **fields: SimpleNamespace(**fields))
    models = {"NPDAUser": NPDAUser, "VisitActivity": VisitActivity}
    apps = SimpleNamespace(get_model=lambda app_label, name: models[name])

    remove_from_models.record_flags_at_removal(apps, None)

    (created,), _ = VisitActivity.objects.bulk_create.call_args
    assert [(a.npdauser_id, a.activity, a.details) for a in created] == [
        (
            1,
            13,
            "RCPCH flags at removal: is_rcpch_audit_team_member=True, is_rcpch_staff=True",
        ),
        (
            2,
            13,
            "RCPCH flags at removal: is_rcpch_audit_team_member=False, is_rcpch_staff=True",
        ),
    ]
