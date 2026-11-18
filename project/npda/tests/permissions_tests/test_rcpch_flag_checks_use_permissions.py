"""
Phase 2 of retiring is_rcpch_audit_team_member and is_rcpch_staff.
See documentation/docs/developer/rcpch-flags-retirement-plan.md

National access now comes from the permissions on the RCPCH audit team group,
not from the flags: a user in the group gets it without the flags, and a flag
on its own no longer grants anything.
"""

from datetime import date
from http import HTTPStatus

import pytest
from django.contrib.auth.models import Group
from django.urls import reverse

from project.constants import (
    AUDIT_CENTRE_COORDINATOR,
    NPDA_AUDIT_TEAM_FULL_ACCESS,
    RCPCH_AUDIT_TEAM,
    TRUST_AUDIT_TEAM_COORDINATOR_ACCESS,
)
from project.npda.models import AuditPeriod
from project.npda.tests.constants_for_tests import ALDER_HEY_PZ_CODE
from project.npda.tests.factories.npda_user_factory import NPDAUserFactory
from project.npda.tests.factories.paediatrics_diabetes_unit_factory import (
    PaediatricsDiabetesUnitFactory,
)
from project.npda.tests.utils import login_and_verify_user

OTHER_PZ_CODE = "PZ130"


def _audit_team_user_without_flags():
    return NPDAUserFactory(
        role=RCPCH_AUDIT_TEAM,
        is_rcpch_audit_team_member=False,
        is_rcpch_staff=False,
        groups=[Group.objects.get(name=NPDA_AUDIT_TEAM_FULL_ACCESS)],
        organisation_employers=[ALDER_HEY_PZ_CODE],
    )


def _coordinator_with_flags():
    return NPDAUserFactory(
        role=AUDIT_CENTRE_COORDINATOR,
        is_rcpch_audit_team_member=True,
        is_rcpch_staff=True,
        groups=[Group.objects.get(name=TRUST_AUDIT_TEAM_COORDINATOR_ACCESS)],
        organisation_employers=[ALDER_HEY_PZ_CODE],
    )


def _other_pdu_patients_url(audit_period):
    PaediatricsDiabetesUnitFactory(pz_code=OTHER_PZ_CODE)
    return reverse(
        "pdu-patients",
        kwargs={"audit_period": audit_period.slug, "pz_code": OTHER_PZ_CODE},
    )


@pytest.mark.django_db
def test_audit_team_group_without_flags_can_view_other_pdu(
    seed_groups_fixture, seed_audit_periods_fixture, client
):
    audit_period = AuditPeriod.objects.get_default_audit_period()
    url = _other_pdu_patients_url(audit_period)
    client = login_and_verify_user(client, _audit_team_user_without_flags())

    assert client.get(url).status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_flags_without_audit_team_group_cannot_view_other_pdu(
    seed_groups_fixture, seed_audit_periods_fixture, client
):
    audit_period = AuditPeriod.objects.get_default_audit_period()
    url = _other_pdu_patients_url(audit_period)
    client = login_and_verify_user(client, _coordinator_with_flags())

    assert client.get(url).status_code == HTTPStatus.FORBIDDEN


@pytest.mark.django_db
def test_hidden_audit_period_needs_permission_not_flag(
    seed_groups_fixture, seed_audit_periods_fixture, client
):
    hidden = AuditPeriod.objects.create(
        is_open=False,
        is_visible=False,
        start_date=date(2030, 4, 1),
        end_date=date(2031, 3, 31),
        slug="2030-2031-hidden-test",
    )
    url = reverse(
        "pdu-patients",
        kwargs={"audit_period": hidden.slug, "pz_code": ALDER_HEY_PZ_CODE},
    )

    flagged_client = login_and_verify_user(client, _coordinator_with_flags())
    assert flagged_client.get(url).status_code == HTTPStatus.FORBIDDEN

    audit_team_client = login_and_verify_user(client, _audit_team_user_without_flags())
    assert audit_team_client.get(url).status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_feature_previews_need_permission_not_flag(
    seed_groups_fixture, seed_audit_periods_fixture, client
):
    url = reverse("feature-flags")

    flagged_client = login_and_verify_user(client, _coordinator_with_flags())
    assert flagged_client.get(url).status_code == HTTPStatus.FORBIDDEN

    audit_team_client = login_and_verify_user(client, _audit_team_user_without_flags())
    assert audit_team_client.get(url).status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_coordinator_cannot_change_email_of_inactive_audit_team_member(
    seed_groups_fixture, seed_audit_periods_fixture, client
):
    """
    has_perm is False for inactive users, so the "is the target an audit team
    member?" check uses role. Otherwise a coordinator in the same PDUs could
    change a deactivated audit team member's email and reactivate them.
    """
    coordinator = NPDAUserFactory(
        role=AUDIT_CENTRE_COORDINATOR,
        groups=[Group.objects.get(name=TRUST_AUDIT_TEAM_COORDINATOR_ACCESS)],
        organisation_employers=[ALDER_HEY_PZ_CODE],
    )
    target = _audit_team_user_without_flags()
    target.is_active = False
    target.save()
    email_before = target.email

    client = login_and_verify_user(client, coordinator)
    client.post(
        reverse("npdauser-update", kwargs={"pk": target.pk}),
        {
            "email": "attacker@example.com",
            "first_name": target.first_name,
            "surname": target.surname,
            "role": target.role,
        },
    )

    target.refresh_from_db()
    assert target.email == email_before
