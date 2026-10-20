"""Tests for the hba1c_stats_by_diabetes_type query."""

import pytest
from dateutil.relativedelta import relativedelta

from project.constants.diabetes_types import DIABETES_TYPES
from project.npda.general_functions.patient_report.queries import (
    hba1c_stats_by_diabetes_type,
)
from project.npda.models import AuditPeriod, NPDAUser, Submission
from project.npda.tests.constants_for_tests import ALDER_HEY_PZ_CODE
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.factories.visit_factory import VisitFactory
from project.npda.tests.UserDataClasses import test_user_rcpch_audit_team_data

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

T1DM = DIABETES_TYPES[0][0]
T2DM = DIABETES_TYPES[1][0]

NONE_STATS = {
    "mean_mmol_mol": None,
    "median_mmol_mol": None,
    "mean_percent": None,
    "median_percent": None,
}


def _get_audit_team_user():
    return NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_rcpch_audit_team_data.role,
    ).first()


def _create_submission(user, audit_period):
    return Submission.objects.create(
        paediatric_diabetes_unit=user.organisation_employers.first(),
        audit_period=audit_period,
        audit_year=audit_period.start_date.year,
        submission_date=audit_period.start_date,
        submission_by=user,
        submission_active=True,
    )


def _add_patient_with_visits(
    submission, audit_period, hba1c_values, diabetes_type=T1DM
):
    """Create a patient with one visit per HbA1c value and add to the submission."""
    patient = PatientFactory(
        diabetes_type=diabetes_type,
        date_of_birth=audit_period.start_date - relativedelta(years=11, days=2),
        diagnosis_date=audit_period.start_date - relativedelta(days=200),
    )
    for i, hba1c in enumerate(hba1c_values):
        VisitFactory(
            patient=patient,
            visit_date=audit_period.start_date + relativedelta(days=10 + i * 90),
            hba1c=hba1c,
            hba1c_date=audit_period.start_date + relativedelta(days=10 + i * 90),
            hba1c_format=1,  # mmol/mol — required for HbA1c normalisation
        )
    submission.patients.add(patient)
    return patient


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_mean_and_median_use_per_patient_medians(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    """KPI 44/45: each patient's median HbA1c first, then mean/median of those.

    patient 1: 40, 50, 90 → per-patient median 50
    patient 2: 70, 80, 90 → per-patient median 80
    per-patient medians [50, 80] → mean 65, median 65
    (the mean/median of all six raw values would be 70/75)
    """
    user = _get_audit_team_user()
    pdu = user.organisation_employers.first()

    audit_period = AuditPeriod.objects.get_default_audit_period()
    submission = _create_submission(user, audit_period)

    _add_patient_with_visits(submission, audit_period, [40, 50, 90])
    _add_patient_with_visits(submission, audit_period, [70, 80, 90])

    result = hba1c_stats_by_diabetes_type(pdu, audit_period)

    assert result["all"]["mean_mmol_mol"] == 65
    assert result["all"]["median_mmol_mol"] == 65
    assert result["t1dm"]["mean_mmol_mol"] == 65
    assert result["t1dm"]["median_mmol_mol"] == 65
    # HbA1c (%) = (0.09148 * HbA1c (mmol/mol)) + 2.152
    assert result["all"]["mean_percent"] == pytest.approx(8.1)
    assert result["all"]["median_percent"] == pytest.approx(8.1)
    # No T2DM or other-type patients
    assert result["t2dm"] == NONE_STATS
    assert result["other"] == NONE_STATS


@pytest.mark.django_db
def test_stratified_by_diabetes_type(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    """t1dm/t2dm/other strata only include patients of that diabetes type."""
    user = _get_audit_team_user()
    pdu = user.organisation_employers.first()

    audit_period = AuditPeriod.objects.get_default_audit_period()
    submission = _create_submission(user, audit_period)

    _add_patient_with_visits(submission, audit_period, [60], diabetes_type=T1DM)
    _add_patient_with_visits(submission, audit_period, [80], diabetes_type=T2DM)
    _add_patient_with_visits(
        submission, audit_period, [90], diabetes_type=DIABETES_TYPES[2][0]
    )

    result = hba1c_stats_by_diabetes_type(pdu, audit_period)

    assert result["t1dm"]["median_mmol_mol"] == 60
    assert result["t2dm"]["median_mmol_mol"] == 80
    assert result["other"]["median_mmol_mol"] == 90
    # "all" is the median of the per-patient medians [60, 80, 90]
    assert result["all"]["median_mmol_mol"] == 80


@pytest.mark.django_db
def test_hba1c_within_90_days_of_diagnosis_excluded(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    """HbA1c measured within 90 days of diagnosis is not a valid value."""
    user = _get_audit_team_user()
    pdu = user.organisation_employers.first()

    audit_period = AuditPeriod.objects.get_default_audit_period()
    submission = _create_submission(user, audit_period)

    # Diagnosed shortly after the audit period start — the only HbA1c
    # measurement is within 90 days of diagnosis, so it is excluded
    patient = PatientFactory(
        diabetes_type=T1DM,
        date_of_birth=audit_period.start_date - relativedelta(years=11, days=2),
        diagnosis_date=audit_period.start_date + relativedelta(days=5),
    )
    VisitFactory(
        patient=patient,
        visit_date=audit_period.start_date + relativedelta(days=10),
        hba1c=60,
        hba1c_date=audit_period.start_date + relativedelta(days=10),
        hba1c_format=1,
    )
    submission.patients.add(patient)

    result = hba1c_stats_by_diabetes_type(pdu, audit_period)

    assert result["all"] == NONE_STATS
    assert result["t1dm"] == NONE_STATS


@pytest.mark.django_db
def test_no_patients_returns_none_for_all_strata(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    """No patients with valid HbA1c values → all strata None."""
    user = _get_audit_team_user()
    pdu = user.organisation_employers.first()

    audit_period = AuditPeriod.objects.get_default_audit_period()

    result = hba1c_stats_by_diabetes_type(pdu, audit_period)

    assert result == {
        "all": NONE_STATS,
        "t1dm": NONE_STATS,
        "t2dm": NONE_STATS,
        "other": NONE_STATS,
    }
