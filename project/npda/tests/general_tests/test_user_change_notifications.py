"""
Changes to sensitive NPDAUser fields are logged in VisitActivity and emailed to
the admins (signals.py). See documentation/docs/developer/users.md.
"""

from unittest.mock import patch

import pytest

from project.constants import AUDIT_CENTRE_COORDINATOR, AUDIT_CENTRE_EDITOR
from project.npda.models import VisitActivity
from project.npda.tests.factories.npda_user_factory import NPDAUserFactory

CHANGED_USER_RECORD = 11
CHANGED_USER_ROLE = 12
CHANGED_ADMIN_FLAG = 13


def _change(user, **fields):
    with patch("project.npda.signals._send_admin_notification") as notify:
        for field, value in fields.items():
            setattr(user, field, value)
        user.save()
    return notify


def _logged(user, activity):
    return VisitActivity.objects.filter(npdauser=user, activity=activity)


@pytest.mark.parametrize("field", ["is_superuser", "is_staff"])
@pytest.mark.django_db
def test_admin_flag_change_is_logged_and_emailed(seed_groups_fixture, field):
    user = NPDAUserFactory(role=AUDIT_CENTRE_EDITOR)

    notify = _change(user, **{field: True})

    notify.assert_called_once()
    assert notify.call_args.args[0] == user
    assert notify.call_args.args[1] == {field: {"old": False, "new": True}}
    assert _logged(user, CHANGED_ADMIN_FLAG).filter(details__contains=field).exists()


@pytest.mark.django_db
def test_role_change_is_logged_and_emailed(seed_groups_fixture):
    user = NPDAUserFactory(role=AUDIT_CENTRE_EDITOR)

    notify = _change(user, role=AUDIT_CENTRE_COORDINATOR)

    notify.assert_called_once()
    assert set(notify.call_args.args[1]) == {"role"}
    assert _logged(user, CHANGED_USER_ROLE).exists()


@pytest.mark.django_db
def test_name_change_is_logged_but_not_emailed(seed_groups_fixture):
    user = NPDAUserFactory(role=AUDIT_CENTRE_EDITOR)

    notify = _change(user, first_name="Renamed")

    notify.assert_not_called()
    assert (
        _logged(user, CHANGED_USER_RECORD)
        .filter(details__contains="first_name")
        .exists()
    )
