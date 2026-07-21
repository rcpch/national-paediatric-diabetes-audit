"""Tests that ensure that views load under normal conditions"""

from http import HTTPStatus

import pytest
from django.test import Client
from django.urls import NoReverseMatch, reverse

from project.npda.models.audit_period import AuditPeriod
from project.npda.models.npda_user import NPDAUser
from project.npda.tests.permissions_tests.test_npda_user_model_actions import (
    ALDER_HEY_PZ_CODE,
)
from project.npda.tests.utils import login_and_verify_user


@pytest.mark.django_db
def test_pt_level_report_loads(seed_groups_fixture, seed_users_fixture, client: Client):
    ah_users = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    )

    ah_user = ah_users.first()

    client = login_and_verify_user(client, ah_user)

    url = reverse("npda_users")
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_dashboard_loads(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture, client: Client
):
    ah_users = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    )

    ah_user = ah_users.first()

    client = login_and_verify_user(client, ah_user)

    audit_period = AuditPeriod.objects.get_default_audit_period()

    url = reverse(
        "pdu-dashboard",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )

    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_login_from_direct_link_to_class_based_view(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture, client: Client
):
    audit_period = AuditPeriod.objects.get_default_audit_period()

    url = reverse(
        "pdu-patients",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )

    response = client.get(url)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse("login") + "?next=" + url


@pytest.mark.django_db
def test_login_from_direct_link_to_function_based_view(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture, client: Client
):
    audit_period = AuditPeriod.objects.get_default_audit_period()

    url = reverse(
        "pdu-dashboard",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )

    response = client.get(url)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse("login") + "?next=" + url

