"""Tests for the all_pdus_t1dm_bubble_map_data query."""

import pytest
from dateutil.relativedelta import relativedelta
from django.contrib.gis.geos import Point

from project.constants.diabetes_types import DIABETES_TYPES
from project.npda.general_functions.patient_report.queries import (
    all_pdus_t1dm_bubble_map_data,
)
from project.npda.models import AuditPeriod, NPDAUser, Submission
from project.npda.tests.UserDataClasses import test_user_rcpch_audit_team_data
from project.npda.tests.constants_for_tests import ALDER_HEY_PZ_CODE
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.factories.visit_factory import VisitFactory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

T1DM = DIABETES_TYPES[0][0]
T2DM = DIABETES_TYPES[1][0]

# Alder Hey's approximate coordinates (lon, lat)
ALDER_HEY_COORDS = Point(-2.9003, 53.4152)


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


def _add_t1dm_patient_with_visit(submission, audit_period, hba1c=60):
    """Create a T1DM patient with a visit and add to the submission."""
    patient = PatientFactory(
        diabetes_type=T1DM,
        date_of_birth=audit_period.start_date - relativedelta(years=11, days=2),
        diagnosis_date=audit_period.start_date - relativedelta(days=200),
    )
    VisitFactory(
        patient=patient,
        visit_date=audit_period.start_date + relativedelta(days=10),
        hba1c=hba1c,
        hba1c_date=audit_period.start_date + relativedelta(days=10),
        hba1c_format=1,  # mmol/mol — required for 2021 dataset HbA1c normalisation
    )
    submission.patients.add(patient)
    return patient


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_returns_empty_list_when_no_submissions(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    """No active submissions → empty list, no crash."""
    audit_period = AuditPeriod.objects.get_default_audit_period()
    result = all_pdus_t1dm_bubble_map_data(audit_period)
    assert result == []


@pytest.mark.django_db
def test_returns_empty_list_when_pdu_has_no_geocoordinates(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    """A submission exists but the PDU has no geocoordinate → excluded from results."""
    user = _get_audit_team_user()
    pdu = user.organisation_employers.first()
    pdu.lead_organisation_geocoordinates = None
    pdu.save()

    audit_period = AuditPeriod.objects.get_default_audit_period()
    submission = _create_submission(user, audit_period)
    _add_t1dm_patient_with_visit(submission, audit_period)

    result = all_pdus_t1dm_bubble_map_data(audit_period)
    assert result == []


@pytest.mark.django_db
def test_returns_entry_for_pdu_with_geocoordinates(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    """PDU with a geocoordinate, one T1DM patient → one entry returned."""
    user = _get_audit_team_user()
    pdu = user.organisation_employers.first()
    pdu.lead_organisation_geocoordinates = ALDER_HEY_COORDS
    pdu.save()

    audit_period = AuditPeriod.objects.get_default_audit_period()
    submission = _create_submission(user, audit_period)
    _add_t1dm_patient_with_visit(submission, audit_period, hba1c=60)

    result = all_pdus_t1dm_bubble_map_data(audit_period)

    assert len(result) == 1
    entry = result[0]
    assert entry["pz_code"] == ALDER_HEY_PZ_CODE
    assert entry["patient_count"] == 1
    assert entry["lat"] == pytest.approx(ALDER_HEY_COORDS.y, abs=0.001)
    assert entry["lon"] == pytest.approx(ALDER_HEY_COORDS.x, abs=0.001)
    assert isinstance(entry["label"], str)


@pytest.mark.django_db
def test_patient_count_reflects_t1dm_only(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    """T2DM patients are excluded from patient_count."""
    user = _get_audit_team_user()
    pdu = user.organisation_employers.first()
    pdu.lead_organisation_geocoordinates = ALDER_HEY_COORDS
    pdu.save()

    audit_period = AuditPeriod.objects.get_default_audit_period()
    submission = _create_submission(user, audit_period)

    # One T1DM patient
    _add_t1dm_patient_with_visit(submission, audit_period, hba1c=60)

    # One T2DM patient — should not be counted
    t2_patient = PatientFactory(
        diabetes_type=T2DM,
        date_of_birth=audit_period.start_date - relativedelta(years=11, days=2),
        diagnosis_date=audit_period.start_date - relativedelta(days=200),
    )
    VisitFactory(
        patient=t2_patient,
        visit_date=audit_period.start_date + relativedelta(days=10),
        hba1c=70,
        hba1c_date=audit_period.start_date + relativedelta(days=10),
    )
    submission.patients.add(t2_patient)

    result = all_pdus_t1dm_bubble_map_data(audit_period)
    assert len(result) == 1
    assert result[0]["patient_count"] == 1


@pytest.mark.django_db
def test_median_hba1c_calculated_correctly(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    """median_hba1c is the median of all T1DM HbA1c values in the period."""
    user = _get_audit_team_user()
    pdu = user.organisation_employers.first()
    pdu.lead_organisation_geocoordinates = ALDER_HEY_COORDS
    pdu.save()

    audit_period = AuditPeriod.objects.get_default_audit_period()
    submission = _create_submission(user, audit_period)

    # Three patients with HbA1c 50, 60, 70 → median = 60
    for hba1c in (50, 60, 70):
        _add_t1dm_patient_with_visit(submission, audit_period, hba1c=hba1c)

    result = all_pdus_t1dm_bubble_map_data(audit_period)
    assert len(result) == 1
    assert result[0]["median_hba1c"] == 60


@pytest.mark.django_db
def test_median_hba1c_is_none_when_no_valid_hba1c(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    """median_hba1c is None when the patient's only HbA1c is within 90 days of diagnosis."""
    user = _get_audit_team_user()
    pdu = user.organisation_employers.first()
    pdu.lead_organisation_geocoordinates = ALDER_HEY_COORDS
    pdu.save()

    audit_period = AuditPeriod.objects.get_default_audit_period()
    submission = _create_submission(user, audit_period)

    # Patient diagnosed very recently — HbA1c within 90 days is excluded
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

    result = all_pdus_t1dm_bubble_map_data(audit_period)
    assert len(result) == 1
    assert result[0]["median_hba1c"] is None


@pytest.mark.django_db
def test_patient_without_visit_in_period_excluded(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    """A patient with no visit inside the audit period does not appear in results."""
    user = _get_audit_team_user()
    pdu = user.organisation_employers.first()
    pdu.lead_organisation_geocoordinates = ALDER_HEY_COORDS
    pdu.save()

    audit_period = AuditPeriod.objects.get_default_audit_period()
    submission = _create_submission(user, audit_period)

    patient = PatientFactory(
        diabetes_type=T1DM,
        date_of_birth=audit_period.start_date - relativedelta(years=11, days=2),
        diagnosis_date=audit_period.start_date - relativedelta(days=200),
    )
    # Visit is outside the audit period
    VisitFactory(
        patient=patient,
        visit_date=audit_period.start_date - relativedelta(days=5),
        hba1c=60,
        hba1c_date=audit_period.start_date - relativedelta(days=5),
        hba1c_format=1,
    )
    submission.patients.add(patient)

    result = all_pdus_t1dm_bubble_map_data(audit_period)
    assert result == []
