"""Tests for the patient report view"""

from decimal import Decimal
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
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.factories.visit_factory import VisitFactory
from project.constants.diabetes_types import DIABETES_TYPES
from project.constants.hba1c_format import HBA1C_FORMATS
from project.npda.views.patient_report.patient_report import TableCategories
from dateutil.relativedelta import relativedelta

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


@pytest.mark.django_db
def _create_outcomes_test_setup(client):
    """Helper function to create common test setup for outcomes tests."""
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

    # Clear existing patients
    Patient.objects.all().delete()

    AUDIT_START_DATE = audit_period.start_date

    # Create eligible criteria (for all diabetes types)
    eligible_criteria = {
        "visit__visit_date": AUDIT_START_DATE + relativedelta(days=2),
        "date_of_birth": AUDIT_START_DATE - relativedelta(days=365 * 10),
        "diagnosis_date": AUDIT_START_DATE - relativedelta(days=2),
        "transfer__date_leaving_service": None,
    }

    return ah_rcpch_audit_team_user, AUDIT_START_DATE, eligible_criteria


@pytest.mark.django_db
def test_outcomes_no_hba1c_measurements(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    """
    Test outcomes view for patient with no HbA1c measurements.

    Verifies that all HbA1c-related fields are None when a patient
    has visits but no HbA1c data recorded.
    """
    ah_rcpch_audit_team_user, AUDIT_START_DATE, eligible_criteria = (
        _create_outcomes_test_setup(client)
    )

    # Create patient with no HbA1c measurements (T1DM)
    patient = PatientFactory(
        nhs_number="1111111111",
        diabetes_type=DIABETES_TYPES[0][0],  # T1DM
        **eligible_criteria,
    )
    # Create a visit without HbA1c
    VisitFactory(
        patient=patient,
        visit_date=AUDIT_START_DATE + relativedelta(days=5),
        hba1c=None,
        hba1c_date=None,
    )

    # Create submission
    submission = Submission.objects.create(
        paediatric_diabetes_unit=ah_rcpch_audit_team_user.organisation_employers.first(),
        audit_year=AUDIT_START_DATE.year,
        submission_date=AUDIT_START_DATE,
        submission_by=ah_rcpch_audit_team_user,
        submission_active=True,
    )
    submission.patients.add(patient)

    # Get the patient report with outcomes category
    response = client.get(
        reverse("patient_report") + f"?category={TableCategories.OUTCOMES.value}",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == HTTPStatus.OK
    assert response.context["selected_category"] == TableCategories.OUTCOMES.value

    patients = response.context["patients"]
    assert len(patients) == 1

    patient_data = patients[0]
    assert patient_data["latest_hba1c_mmol_mol"] is None
    assert patient_data["latest_hba1c_pct"] is None
    assert patient_data["previous_to_latest_hba1c_mmol_mol"] is None
    assert patient_data["previous_to_latest_hba1c_pct"] is None
    assert patient_data["hba1c_delta"] is None
    assert patient_data["latest_hba1c_date"] is None
    assert patient_data["previous_to_latest_hba1c_date"] is None
    assert patient_data["days_delta_between_latest_and_previous_hba1c"] is None


@pytest.mark.django_db
def test_outcomes_single_hba1c_measurement(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    """
    Test outcomes view for patient with single HbA1c measurement.

    Verifies that latest HbA1c values are populated correctly while
    previous values remain None, and no delta calculations are performed.
    """
    ah_rcpch_audit_team_user, AUDIT_START_DATE, eligible_criteria = (
        _create_outcomes_test_setup(client)
    )

    # Create patient with single HbA1c measurement (T2DM)
    patient = PatientFactory(
        nhs_number="2222222222",
        diabetes_type=DIABETES_TYPES[1][0],  # T2DM
        **eligible_criteria,
    )
    VisitFactory(
        patient=patient,
        visit_date=AUDIT_START_DATE + relativedelta(days=5),
        hba1c=50,  # 50 mmol/mol
        hba1c_format=HBA1C_FORMATS[0][0],  # mmol/mol format
        hba1c_date=AUDIT_START_DATE + relativedelta(days=5),
    )

    # Create submission
    submission = Submission.objects.create(
        paediatric_diabetes_unit=ah_rcpch_audit_team_user.organisation_employers.first(),
        audit_year=AUDIT_START_DATE.year,
        submission_date=AUDIT_START_DATE,
        submission_by=ah_rcpch_audit_team_user,
        submission_active=True,
    )
    submission.patients.add(patient)

    # Get the patient report with outcomes category
    response = client.get(
        reverse("patient_report") + f"?category={TableCategories.OUTCOMES.value}",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == HTTPStatus.OK
    assert response.context["selected_category"] == TableCategories.OUTCOMES.value

    patients = response.context["patients"]
    assert len(patients) == 1

    patient_data = patients[0]
    assert patient_data["latest_hba1c_mmol_mol"] == 50
    # Calculate expected percentage: (0.09148 * 50) + 2.152 = 6.726
    EXPECTED_PCT = Decimal((0.09148 * 50) + 2.152)
    assert abs(patient_data["latest_hba1c_pct"] - EXPECTED_PCT) < 0.01
    assert patient_data["previous_to_latest_hba1c_mmol_mol"] is None
    assert patient_data["previous_to_latest_hba1c_pct"] is None
    assert patient_data["hba1c_delta"] is None
    assert patient_data["latest_hba1c_date"] == AUDIT_START_DATE + relativedelta(days=5)
    assert patient_data["previous_to_latest_hba1c_date"] is None
    assert patient_data["days_delta_between_latest_and_previous_hba1c"] is None


@pytest.mark.django_db
def test_outcomes_multiple_hba1c_measurements(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    """
    Test outcomes view for patient with multiple HbA1c measurements.

    Verifies that both latest and previous HbA1c values are populated correctly,
    percentage conversions are accurate, and delta calculations show the
    percentage change between measurements.
    """
    ah_rcpch_audit_team_user, AUDIT_START_DATE, eligible_criteria = (
        _create_outcomes_test_setup(client)
    )

    # Create patient with multiple HbA1c measurements (Other/MODY)
    patient = PatientFactory(
        nhs_number="3333333333",
        diabetes_type=DIABETES_TYPES[2][0],  # Other specified diabetes/MODY
        **eligible_criteria,
    )
    # prev hba1c
    VisitFactory(
        patient=patient,
        visit_date=AUDIT_START_DATE + relativedelta(days=10),
        hba1c=60,  # 60 mmol/mol
        hba1c_format=HBA1C_FORMATS[0][0],  # mmol/mol format
        hba1c_date=AUDIT_START_DATE + relativedelta(days=10),
    )
    # Latest hba1c
    VisitFactory(
        patient=patient,
        visit_date=AUDIT_START_DATE + relativedelta(days=20),
        hba1c=45,  # 45 mmol/mol
        hba1c_format=HBA1C_FORMATS[0][0],  # mmol/mol format
        hba1c_date=AUDIT_START_DATE + relativedelta(days=20),
    )

    # Create submission
    submission = Submission.objects.create(
        paediatric_diabetes_unit=ah_rcpch_audit_team_user.organisation_employers.first(),
        audit_year=AUDIT_START_DATE.year,
        submission_date=AUDIT_START_DATE,
        submission_by=ah_rcpch_audit_team_user,
        submission_active=True,
    )
    submission.patients.add(patient)

    # Get the patient report with outcomes category
    response = client.get(
        reverse("patient_report") + f"?category={TableCategories.OUTCOMES.value}",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == HTTPStatus.OK
    assert response.context["selected_category"] == TableCategories.OUTCOMES.value

    patients = response.context["patients"]
    assert len(patients) == 1

    patient_data = patients[0]
    assert patient_data["latest_hba1c_mmol_mol"] == 45  # Latest value
    EXPECTED_PCT = Decimal((0.09148 * 45) + 2.152)
    assert abs(patient_data["latest_hba1c_pct"] - EXPECTED_PCT) < 0.01
    assert patient_data["previous_to_latest_hba1c_mmol_mol"] == 60  # Previous value
    EXPECTED_PCT = Decimal((0.09148 * 60) + 2.152)
    assert abs(patient_data["previous_to_latest_hba1c_pct"] - EXPECTED_PCT) < 0.01
    # Calculate expected delta: ((45 - 60) / 60) * 100 = -25.0
    expected_delta = round(((45 - 60) / 60) * 100, 1)
    assert patient_data["hba1c_delta"] == expected_delta
    assert patient_data["latest_hba1c_date"] == AUDIT_START_DATE + relativedelta(
        days=20
    )
    assert patient_data[
        "previous_to_latest_hba1c_date"
    ] == AUDIT_START_DATE + relativedelta(days=10)
    assert patient_data["days_delta_between_latest_and_previous_hba1c"] == 10
