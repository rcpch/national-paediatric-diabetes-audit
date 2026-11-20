"""
RCPCH audit team permissions and the group that holds them.
See documentation/docs/developer/users.md

- Only the RCPCH audit team group holds the national access permissions.
- Changing a role, in the app or the Django admin, moves the user to the role's group.
- Joining the audit team group logs and emails the admins.
- The group seeder, run on every deploy by s/start-prod, adds new permissions
  to existing groups.
"""

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group
from django.test import RequestFactory
from django.urls import reverse

from project.constants import (
    AUDIT_CENTRE_COORDINATOR,
    AUDIT_CENTRE_EDITOR,
    CAN_ACCESS_ALL_PDUS,
    CAN_ASSIGN_RCPCH_AUDIT_TEAM_ROLE,
    CAN_EDIT_CLOSED_AUDIT_PERIODS,
    CAN_MANAGE_INACTIVE_PDUS,
    CAN_MANAGE_USERS_IN_ANY_PDU,
    CAN_OVERRIDE_DATA_UPLOAD_RULES,
    CAN_PREVIEW_FEATURES,
    CAN_RESET_USER_TWO_FACTOR,
    CAN_VIEW_HIDDEN_AUDIT_PERIODS,
    NPDA_AUDIT_TEAM_FULL_ACCESS,
    PATIENT_ACCESS,
    RCPCH_AUDIT_TEAM,
    TRUST_AUDIT_TEAM_COORDINATOR_ACCESS,
    TRUST_AUDIT_TEAM_EDIT_ACCESS,
    TRUST_AUDIT_TEAM_VIEW_ONLY,
)
from project.npda.admin import NPDAUserAdmin
from project.npda.management.commands.create_groups import groups_seeder
from project.npda.models import NPDAUser, VisitActivity
from project.npda.tests.constants_for_tests import ALDER_HEY_PZ_CODE
from project.npda.tests.factories.npda_user_factory import NPDAUserFactory
from project.npda.tests.utils import login_and_verify_user

RCPCH_AUDIT_TEAM_ONLY_PERMISSIONS = {
    CAN_ACCESS_ALL_PDUS[0],
    CAN_MANAGE_INACTIVE_PDUS[0],
    CAN_VIEW_HIDDEN_AUDIT_PERIODS[0],
    CAN_EDIT_CLOSED_AUDIT_PERIODS[0],
    CAN_OVERRIDE_DATA_UPLOAD_RULES[0],
    CAN_MANAGE_USERS_IN_ANY_PDU[0],
    CAN_ASSIGN_RCPCH_AUDIT_TEAM_ROLE[0],
    CAN_RESET_USER_TWO_FACTOR[0],
    CAN_PREVIEW_FEATURES[0],
    "view_banner",
}


def _group(name):
    return Group.objects.get(name=name)


def _codenames(group):
    return set(group.permissions.values_list("codename", flat=True))


def _group_names(user):
    return set(user.groups.values_list("name", flat=True))


# Permissions


@pytest.mark.django_db
def test_audit_team_group_has_national_access_permissions(seed_groups_fixture):
    assert RCPCH_AUDIT_TEAM_ONLY_PERMISSIONS <= _codenames(
        _group(NPDA_AUDIT_TEAM_FULL_ACCESS)
    )


@pytest.mark.parametrize(
    "group_name",
    [
        TRUST_AUDIT_TEAM_VIEW_ONLY,
        TRUST_AUDIT_TEAM_EDIT_ACCESS,
        TRUST_AUDIT_TEAM_COORDINATOR_ACCESS,
        PATIENT_ACCESS,
    ],
)
@pytest.mark.django_db
def test_other_groups_lack_national_access_permissions(seed_groups_fixture, group_name):
    assert not RCPCH_AUDIT_TEAM_ONLY_PERMISSIONS & _codenames(_group(group_name))


@pytest.mark.django_db
def test_audit_team_member_has_permissions_via_role(seed_groups_fixture):
    user = NPDAUserFactory(
        role=RCPCH_AUDIT_TEAM, groups=[_group(NPDA_AUDIT_TEAM_FULL_ACCESS)]
    )

    assert user.has_perm(f"npda.{CAN_ACCESS_ALL_PDUS[0]}")
    assert user.has_perm("npda.view_banner")


@pytest.mark.django_db
def test_seeder_adds_new_permissions_to_existing_group(seed_groups_fixture):
    """
    Deploys run the seeder against existing groups, so it must add permissions
    that are missing from them, not only seed groups it creates.
    """
    group = _group(NPDA_AUDIT_TEAM_FULL_ACCESS)
    group.permissions.remove(
        *group.permissions.filter(codename__in=RCPCH_AUDIT_TEAM_ONLY_PERMISSIONS)
    )

    groups_seeder(verbose=False)

    assert RCPCH_AUDIT_TEAM_ONLY_PERMISSIONS <= _codenames(group)


@pytest.mark.django_db
def test_seeder_creates_missing_group(seed_groups_fixture):
    _group(PATIENT_ACCESS).delete()

    groups_seeder(verbose=False)

    assert "view_patient" in _codenames(_group(PATIENT_ACCESS))


@pytest.mark.django_db
def test_seeder_does_not_add_permissions_to_other_groups(seed_groups_fixture):
    groups_seeder(verbose=False)
    groups_seeder(verbose=False)

    for name in (
        TRUST_AUDIT_TEAM_VIEW_ONLY,
        TRUST_AUDIT_TEAM_EDIT_ACCESS,
        TRUST_AUDIT_TEAM_COORDINATOR_ACCESS,
        PATIENT_ACCESS,
    ):
        assert not RCPCH_AUDIT_TEAM_ONLY_PERMISSIONS & _codenames(_group(name))


# Changing role in the app


@pytest.mark.django_db
def test_changing_role_in_edit_user_view_moves_group(
    seed_groups_fixture, seed_users_fixture, client
):
    """
    Regression test: before April 2025 the edit-user view changed the role but
    left the user in their old group.
    """
    audit_team_user = NPDAUser.objects.filter(
        role=RCPCH_AUDIT_TEAM,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()
    client = login_and_verify_user(client, audit_team_user)

    user = NPDAUserFactory(
        role=AUDIT_CENTRE_EDITOR,
        groups=[_group(TRUST_AUDIT_TEAM_EDIT_ACCESS)],
        organisation_employers=[ALDER_HEY_PZ_CODE],
    )

    response = client.post(
        reverse("npdauser-update", kwargs={"pk": user.pk}),
        {
            "email": user.email,
            "first_name": user.first_name,
            "surname": user.surname,
            "role": AUDIT_CENTRE_COORDINATOR,
        },
    )
    assert response.status_code == 302

    user.refresh_from_db()
    assert user.role == AUDIT_CENTRE_COORDINATOR
    assert _group_names(user) == {TRUST_AUDIT_TEAM_COORDINATOR_ACCESS}


# Changing role in the Django admin


def _admin_save(user, changed_data, change=True):
    request = RequestFactory().post("/")
    request.user = user
    NPDAUserAdmin(NPDAUser, AdminSite()).save_model(
        request, user, SimpleNamespace(changed_data=changed_data), change
    )
    user.refresh_from_db()


@pytest.mark.django_db
def test_admin_promotion_syncs_group(seed_groups_fixture):
    user = NPDAUserFactory(
        role=AUDIT_CENTRE_COORDINATOR,
        groups=[_group(TRUST_AUDIT_TEAM_EDIT_ACCESS)],
    )

    user.role = RCPCH_AUDIT_TEAM
    _admin_save(user, ["role"])

    assert _group_names(user) == {NPDA_AUDIT_TEAM_FULL_ACCESS}


@pytest.mark.django_db
def test_admin_demotion_moves_group(seed_groups_fixture):
    user = NPDAUserFactory(
        role=RCPCH_AUDIT_TEAM,
        groups=[_group(NPDA_AUDIT_TEAM_FULL_ACCESS)],
    )

    user.role = AUDIT_CENTRE_COORDINATOR
    _admin_save(user, ["role"])

    assert _group_names(user) == {TRUST_AUDIT_TEAM_COORDINATOR_ACCESS}


@pytest.mark.django_db
def test_admin_edit_without_role_change_leaves_groups(seed_groups_fixture):
    user = NPDAUserFactory(
        role=AUDIT_CENTRE_COORDINATOR,
        groups=[_group(TRUST_AUDIT_TEAM_EDIT_ACCESS)],
    )

    user.first_name = "Renamed"
    _admin_save(user, ["first_name"])

    assert user.first_name == "Renamed"
    assert _group_names(user) == {TRUST_AUDIT_TEAM_EDIT_ACCESS}


@pytest.mark.django_db
def test_admin_form_does_not_edit_groups(seed_groups_fixture):
    """
    The admin saves m2m fields after save_model, so an editable groups field
    would undo the sync.
    """
    request = RequestFactory().get("/")
    request.user = NPDAUserFactory(role=RCPCH_AUDIT_TEAM, is_superuser=True)
    form = NPDAUserAdmin(NPDAUser, AdminSite()).get_form(request)

    assert "groups" not in form.base_fields
    assert "role" in form.base_fields


# Alert on joining the audit team group


@pytest.mark.django_db
def test_joining_audit_team_group_notifies_admins(seed_groups_fixture):
    user = NPDAUserFactory(
        role=AUDIT_CENTRE_COORDINATOR,
        groups=[_group(TRUST_AUDIT_TEAM_COORDINATOR_ACCESS)],
    )

    with patch("project.npda.signals._send_admin_notification") as notify:
        user.groups.set([_group(NPDA_AUDIT_TEAM_FULL_ACCESS)])

    notify.assert_called_once()
    assert notify.call_args.args[0] == user
    assert VisitActivity.objects.filter(
        npdauser=user, activity=13, details__contains=NPDA_AUDIT_TEAM_FULL_ACCESS
    ).exists()


@pytest.mark.django_db
def test_joining_audit_team_group_from_group_side_notifies_admins(
    seed_groups_fixture,
):
    user = NPDAUserFactory(role=AUDIT_CENTRE_COORDINATOR)

    with patch("project.npda.signals._send_admin_notification") as notify:
        _group(NPDA_AUDIT_TEAM_FULL_ACCESS).user_set.add(user)

    notify.assert_called_once()
    assert notify.call_args.args[0] == user


@pytest.mark.django_db
def test_resyncing_existing_member_does_not_notify(seed_groups_fixture):
    user = NPDAUserFactory(
        role=RCPCH_AUDIT_TEAM, groups=[_group(NPDA_AUDIT_TEAM_FULL_ACCESS)]
    )

    with patch("project.npda.signals._send_admin_notification") as notify:
        user.groups.set([_group(NPDA_AUDIT_TEAM_FULL_ACCESS)])

    notify.assert_not_called()


@pytest.mark.django_db
def test_leaving_audit_team_role_notifies_admins(seed_groups_fixture):
    """
    Joining the audit team group has its own alert. Leaving it is reported by
    the role change, which must email the admins.
    """
    user = NPDAUserFactory(
        role=RCPCH_AUDIT_TEAM, groups=[_group(NPDA_AUDIT_TEAM_FULL_ACCESS)]
    )

    with patch("project.npda.signals._send_admin_notification") as notify:
        user.role = AUDIT_CENTRE_COORDINATOR
        user.save()

    notify.assert_called_once()
    assert notify.call_args.args[0] == user
    assert notify.call_args.args[1]["role"] == {
        "old": RCPCH_AUDIT_TEAM,
        "new": AUDIT_CENTRE_COORDINATOR,
    }


@pytest.mark.django_db
def test_joining_another_group_does_not_notify(seed_groups_fixture):
    user = NPDAUserFactory(role=AUDIT_CENTRE_EDITOR)

    with patch("project.npda.signals._send_admin_notification") as notify:
        user.groups.add(_group(TRUST_AUDIT_TEAM_EDIT_ACCESS))

    notify.assert_not_called()
