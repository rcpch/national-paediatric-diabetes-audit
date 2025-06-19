"""Tests for the patient report view"""

import logging
from http import HTTPStatus

# Python imports
import pytest
from django.db.models import Count

# 3rd party imports
from django.urls import reverse

from project.npda.general_functions.data_generator_extended import (
    AgeRange,
    FakePatientCreator,
    HbA1cTargetRange,
    VisitType,
)

# E12 imports
from project.npda.models import NPDAUser
from project.npda.models.audit_period import AuditPeriod
from project.npda.models.patient import Patient
from project.npda.models.submission import Submission
from project.npda.tests.constants_for_tests import ALDER_HEY_PZ_CODE
from project.npda.tests.factories import test_user_rcpch_audit_team_data
from project.npda.tests.utils import login_and_verify_user
from project.npda.urls import patient_report_urlpatterns

logger = logging.getLogger(__name__)


def test_anonymous_user_cannot_access_patient_report(
    client,
):
    """Anonymous users should not be able to access the patient report."""

    for url in patient_report_urlpatterns:
        response = client.get(reverse(url.name))
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("login") + "?next=" + reverse(url.name)


@pytest.mark.django_db
def test_no_duplicate_patients_in_report(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    """Seeds a bunch of patients and checks that there are no duplicates."""

    # Login as RCPCH Audit Team user
    ah_rcpch_audit_team_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_rcpch_audit_team_data.role,
    ).first()
    client = login_and_verify_user(client, ah_rcpch_audit_team_user)

    # Get audit period and ensure it's open
    audit_period = AuditPeriod.objects.get_default_audit_period()
    audit_period.is_open = True
    audit_period.save()

    # Create fake patients and visits using FakePatientCreator
    fake_patient_creator = FakePatientCreator(
        audit_start_date=audit_period.start_date,
        audit_end_date=audit_period.end_date,
    )

    # Create 10 patients with visits
    N_PATIENTS = 10
    new_pts = fake_patient_creator.create_and_save_fake_patients(
        n=N_PATIENTS,
        age_range=AgeRange.AGE_11_15,
        hb1ac_target_range=HbA1cTargetRange.TARGET,
        visit_types=[VisitType.CLINIC, VisitType.CLINIC],
        visit_kwargs={"is_valid": True},
    )

    new_submission = Submission.objects.create(
        paediatric_diabetes_unit=ah_rcpch_audit_team_user.organisation_employers.first(),
        audit_year=audit_period.start_date.year,
        submission_date=audit_period.start_date,
        submission_by=ah_rcpch_audit_team_user,
        submission_active=True,
    )

    # Add patients to submission
    new_submission.patients.add(*new_pts)

    # Get the patient report
    response = client.get(reverse("patient_report"))
    assert response.status_code == HTTPStatus.OK

    assert isinstance(response.context["patients"], list)
    assert len(response.context["patients"]) == N_PATIENTS

    # Check that there are no duplicate patients
    duplicates = set(
        patient["patient_identifier"] for patient in response.context["patients"]
    )
    assert len(duplicates) == N_PATIENTS

def test_outcomes_values_are_as_expected(seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    """Uses known hba1c measurements to assert expected values"""

    # Login as RCPCH Audit Team user
    ah_rcpch_audit_team_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_rcpch_audit_team_data.role,
    ).first()
    client = login_and_verify_user(client, ah_rcpch_audit_team_user)

    # Get audit period and ensure it's open
    audit_period = AuditPeriod.objects.get_default_audit_period()
    audit_period.is_open = True
    audit_period.save()

    # Create fake patients and visits using FakePatientCreator
    fake_patient_creator = FakePatientCreator(
        audit_start_date=audit_period.start_date,
        audit_end_date=audit_period.end_date,
    )

    # Create 10 patients with visits
    N_PATIENTS = 10
    new_pts = fake_patient_creator.create_and_save_fake_patients(
        n=N_PATIENTS,
        age_range=AgeRange.AGE_11_15,
        hb1ac_target_range=HbA1cTargetRange.TARGET,
        visit_types=[VisitType.CLINIC, VisitType.CLINIC],
        visit_kwargs={"is_valid": True},
    )

    new_submission = Submission.objects.create(
        paediatric_diabetes_unit=ah_rcpch_audit_team_user.organisation_employers.first(),
        audit_year=audit_period.start_date.year,
        submission_date=audit_period.start_date,
        submission_by=ah_rcpch_audit_team_user,
        submission_active=True,
    )

    # Add patients to submission
    new_submission.patients.add(*new_pts)

    # Get the patient report
    response = client.get(reverse("patient_report"))
    assert response.status_code == HTTPStatus.OK