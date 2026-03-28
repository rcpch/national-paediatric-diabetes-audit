import pytest
from django.urls import reverse

from project.npda.models import NPDAUser
from project.npda.tests.constants_for_tests import ALDER_HEY_PZ_CODE
from project.npda.tests.factories.npda_user_factory import NPDAUserFactory
from project.npda.tests.UserDataClasses import (
    test_user_audit_centre_editor_data,
    test_user_rcpch_audit_team_data,
)
from project.npda.tests.utils import login_and_verify_user


@pytest.mark.django_db
def test_feature_flags_visible_to_audit_team(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture, client
):
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_rcpch_audit_team_data.role,
    ).first()
    client = login_and_verify_user(client, user)

    response = client.get(reverse("feature-flags"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_feature_flags_visible_to_superuser(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture, client
):
    user = NPDAUserFactory(
        is_superuser=True,
        is_staff=True,
        is_active=True,
        role=test_user_rcpch_audit_team_data.role,
        organisation_employers=[ALDER_HEY_PZ_CODE],
        groups=[test_user_audit_centre_editor_data.group_name],
    )
    client = login_and_verify_user(client, user)

    response = client.get(reverse("feature-flags"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_feature_flags_hidden_from_non_audit_users(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture, client
):
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()
    client = login_and_verify_user(client, user)

    response = client.get(reverse("feature-flags"))

    assert response.status_code == 403
