"""Tests for the dashboard query functions that replace CalculateKPIS in the dashboard views.

These tests are written TDD-style against functions that will be added to
project/npda/general_functions/patient_report/queries.py as part of the dashboard
refactor (see views/dashboard/PLAN.md).

The imports from queries.py will fail until those functions are implemented — that
is expected and intentional.

2021 dataset audit period: 2024-04-01 → 2025-03-31 (start_date < 2026-04-01)
2026 dataset audit period: 2026-04-01 → 2027-03-31 (start_date >= 2026-04-01)
"""

import logging

import pytest
from dateutil.relativedelta import relativedelta

from project.constants.closed_loop_types import CLOSED_LOOP_TYPES
from project.constants.diabetes_types import DIABETES_TYPES
from project.constants.glucose_monitoring_types import GLUCOSE_MONITORING_TYPES
from project.constants.hospital_admission_reasons import HOSPITAL_ADMISSION_REASONS
from project.npda.general_functions.patient_report.queries import (
    count_admissions,
    count_cgm_use,
    count_eligible_patients,
    count_hcl_use,
    count_new_diagnoses_by_quarter,
    count_pump_use,
    dashboard_health_check_totals,
)
from project.npda.models import AuditPeriod, NPDAUser, Submission
from project.npda.tests.constants_for_tests import ALDER_HEY_PZ_CODE
from project.npda.tests.factories import test_user_audit_centre_editor_data
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.factories.visit_factory import VisitFactory

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_user_and_pdu():
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()
    pdu = user.organisation_employers.first()
    return user, pdu


def _create_submission(user, pdu, audit_period):
    return Submission.objects.create(
        paediatric_diabetes_unit=pdu,
        audit_period=audit_period,
        audit_year=audit_period.start_date.year,
        submission_date=audit_period.start_date,
        submission_by=user,
        submission_active=True,
    )


# ---------------------------------------------------------------------------
# count_eligible_patients
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_count_eligible_patients_counts_all_diabetes_types(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    """count_eligible_patients includes T1DM and T2DM patients (all diabetes types)."""
    user, pdu = _get_user_and_pdu()
    audit_period = AuditPeriod.objects.get(slug="2024-2025")
    visit_date = audit_period.start_date + relativedelta(days=10)

    t1 = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )
    t2 = PatientFactory(
        diabetes_type=DIABETES_TYPES[1][0],
        date_of_birth=audit_period.start_date - relativedelta(years=12),
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )
    VisitFactory(patient=t1, visit_date=visit_date)
    VisitFactory(patient=t2, visit_date=visit_date)

    submission = _create_submission(user, pdu, audit_period)
    submission.patients.add(t1, t2)

    assert count_eligible_patients(pdu, audit_period) == 2


@pytest.mark.django_db
def test_count_eligible_patients_excludes_patient_over_25(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    """A patient aged 25+ at audit start is excluded from the eligible count."""
    user, pdu = _get_user_and_pdu()
    audit_period = AuditPeriod.objects.get(slug="2024-2025")
    visit_date = audit_period.start_date + relativedelta(days=10)

    young = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )
    too_old = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=26),
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )
    VisitFactory(patient=young, visit_date=visit_date)
    VisitFactory(patient=too_old, visit_date=visit_date)

    submission = _create_submission(user, pdu, audit_period)
    submission.patients.add(young, too_old)

    assert count_eligible_patients(pdu, audit_period) == 1


@pytest.mark.django_db
def test_count_eligible_patients_excludes_patient_with_no_visit_in_audit_period(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    """A patient whose only visit is outside the audit period is excluded."""
    user, pdu = _get_user_and_pdu()
    audit_period = AuditPeriod.objects.get(slug="2024-2025")

    with_visit = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )
    no_visit_in_range = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )
    VisitFactory(
        patient=with_visit,
        visit_date=audit_period.start_date + relativedelta(days=10),
    )
    VisitFactory(
        patient=no_visit_in_range,
        visit_date=audit_period.start_date - relativedelta(days=10),  # before range
    )

    submission = _create_submission(user, pdu, audit_period)
    submission.patients.add(with_visit, no_visit_in_range)

    assert count_eligible_patients(pdu, audit_period) == 1


# ---------------------------------------------------------------------------
# count_new_diagnoses_by_quarter
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_count_new_diagnoses_by_quarter_returns_correct_structure(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    """Return value is a dict keyed 1..N with total_passed/total_eligible/pct."""
    user, pdu = _get_user_and_pdu()
    # Use a completed audit period so all 4 quarters are returned.
    audit_period = AuditPeriod.objects.get(slug="2024-2025")

    patient = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        diagnosis_date=audit_period.start_date + relativedelta(days=5),  # Q1
    )
    VisitFactory(
        patient=patient,
        visit_date=audit_period.start_date + relativedelta(days=10),
    )

    submission = _create_submission(user, pdu, audit_period)
    submission.patients.add(patient)

    result = count_new_diagnoses_by_quarter(pdu, audit_period)

    assert isinstance(result, dict)
    assert set(result.keys()) == {1, 2, 3, 4}
    for q_data in result.values():
        assert "total_passed" in q_data
        assert "total_eligible" in q_data
        assert "pct" in q_data


@pytest.mark.django_db
def test_count_new_diagnoses_by_quarter_q1_patient_appears_in_q1(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    """A patient diagnosed in Q1 is counted in Q1 and all subsequent quarters."""
    user, pdu = _get_user_and_pdu()
    audit_period = AuditPeriod.objects.get(slug="2024-2025")

    # Diagnosis in Q1 (April 2024)
    patient = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        diagnosis_date=audit_period.start_date + relativedelta(days=5),
    )
    VisitFactory(
        patient=patient,
        visit_date=audit_period.start_date + relativedelta(days=10),
    )

    submission = _create_submission(user, pdu, audit_period)
    submission.patients.add(patient)

    result = count_new_diagnoses_by_quarter(pdu, audit_period)

    assert result[1]["total_passed"] == 1
    assert result[1]["total_eligible"] == 1


# ---------------------------------------------------------------------------
# count_hcl_use — 2021 dataset
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_count_hcl_use_2021_pump_with_hcl_closed_loop_is_passed(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    """2021 dataset: treatment=3 (pump) + closed_loop_system=2 (licensed HCL) → passed."""
    user, pdu = _get_user_and_pdu()
    audit_period = AuditPeriod.objects.get(slug="2024-2025")
    visit_date = audit_period.start_date + relativedelta(days=10)

    on_hcl = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )
    not_on_hcl = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )
    VisitFactory(
        patient=on_hcl,
        visit_date=visit_date,
        treatment=3,  # insulin pump
        closed_loop_system=CLOSED_LOOP_TYPES[1][0],  # 2 = licensed
    )
    VisitFactory(
        patient=not_on_hcl,
        visit_date=visit_date,
        treatment=3,  # insulin pump
        closed_loop_system=CLOSED_LOOP_TYPES[0][0],  # 1 = No
    )

    submission = _create_submission(user, pdu, audit_period)
    submission.patients.add(on_hcl, not_on_hcl)

    passed, eligible = count_hcl_use(pdu, audit_period)

    assert passed == 1
    assert eligible == 2


@pytest.mark.django_db
def test_count_hcl_use_2021_non_pump_patient_not_passed(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    """2021 dataset: patient on injections only (treatment=2) is not passed for HCL."""
    user, pdu = _get_user_and_pdu()
    audit_period = AuditPeriod.objects.get(slug="2024-2025")
    visit_date = audit_period.start_date + relativedelta(days=10)

    patient = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )
    VisitFactory(
        patient=patient,
        visit_date=visit_date,
        treatment=2,  # four+ injections/day — not a pump
        closed_loop_system=None,
    )

    submission = _create_submission(user, pdu, audit_period)
    submission.patients.add(patient)

    passed, eligible = count_hcl_use(pdu, audit_period)

    assert passed == 0
    assert eligible == 1


# ---------------------------------------------------------------------------
# count_hcl_use — 2026 dataset
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_count_hcl_use_2026_insulin_regimen_5_is_passed(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    """2026 dataset: insulin_regimen=5 (Hybrid closed loop) → passed."""
    user, pdu = _get_user_and_pdu()
    audit_period = AuditPeriod.objects.get(slug="2026-2027")
    visit_date = audit_period.start_date + relativedelta(days=10)

    on_hcl = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )
    on_pump_only = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )
    VisitFactory(
        patient=on_hcl,
        visit_date=visit_date,
        treatment=None,
        closed_loop_system=None,
        glucose_monitoring=None,
        insulin_regimen=5,  # Hybrid closed loop
    )
    VisitFactory(
        patient=on_pump_only,
        visit_date=visit_date,
        treatment=None,
        closed_loop_system=None,
        glucose_monitoring=None,
        insulin_regimen=4,  # Insulin pump (standalone)
    )

    submission = _create_submission(user, pdu, audit_period)
    submission.patients.add(on_hcl, on_pump_only)

    passed, eligible = count_hcl_use(pdu, audit_period)

    assert passed == 1
    assert eligible == 2


# ---------------------------------------------------------------------------
# count_hcl_use — regression: patients who reverted from HCL
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_count_hcl_use_2021_reverted_patient_excluded_from_total(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    """
    2021 dataset regression: a patient whose earliest visit was HCL (pump +
    closed loop) but whose most recent treatment visit is back on injections
    must NOT be counted in the HCL total.

    Three patients:
      - currently_on_hcl:  latest visit = pump + licensed closed loop → passed
      - reverted_to_injections: earlier visit = pump + licensed closed loop,
                                 latest visit = injections               → NOT passed
      - never_on_hcl:     only ever on injections                       → NOT passed

    Expected: passed=1, eligible=3
    """
    user, pdu = _get_user_and_pdu()
    audit_period = AuditPeriod.objects.get(slug="2024-2025")
    visit_date = audit_period.start_date + relativedelta(days=10)

    currently_on_hcl = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )
    reverted_to_injections = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )
    never_on_hcl = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )

    # currently_on_hcl: single visit, pump + closed loop
    VisitFactory(
        patient=currently_on_hcl,
        visit_date=visit_date,
        treatment=3,  # insulin pump
        closed_loop_system=CLOSED_LOOP_TYPES[1][0],  # 2 = licensed
    )

    # reverted_to_injections: first visit was HCL, latest is injections
    VisitFactory(
        patient=reverted_to_injections,
        visit_date=visit_date,
        treatment=3,  # pump
        closed_loop_system=CLOSED_LOOP_TYPES[1][0],  # 2 = licensed
    )
    VisitFactory(
        patient=reverted_to_injections,
        visit_date=visit_date + relativedelta(days=90),
        treatment=2,  # four or more injections/day — no longer on pump
        closed_loop_system=CLOSED_LOOP_TYPES[0][0],  # 1 = No
    )

    # never_on_hcl: only ever on injections
    VisitFactory(
        patient=never_on_hcl,
        visit_date=visit_date,
        treatment=2,
        closed_loop_system=CLOSED_LOOP_TYPES[0][0],  # 1 = No
    )

    submission = _create_submission(user, pdu, audit_period)
    submission.patients.add(currently_on_hcl, reverted_to_injections, never_on_hcl)

    passed, eligible = count_hcl_use(pdu, audit_period)

    assert eligible == 3
    assert passed == 1  # only currently_on_hcl passes


@pytest.mark.django_db
def test_count_hcl_use_2021_closed_loop_on_older_visit_not_counted(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    """
    2021 dataset regression: a patient whose latest treatment visit records a
    pump but has no closed_loop_system value (None) on that visit must NOT be
    counted, even if an older visit recorded a closed loop system.

    The closed_loop_system value must come from the same visit as the latest
    treatment.
    """
    user, pdu = _get_user_and_pdu()
    audit_period = AuditPeriod.objects.get(slug="2024-2025")
    visit_date = audit_period.start_date + relativedelta(days=10)

    patient = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )

    # Older visit: pump + closed loop recorded
    VisitFactory(
        patient=patient,
        visit_date=visit_date,
        treatment=3,
        closed_loop_system=CLOSED_LOOP_TYPES[1][0],  # 2 = licensed
    )
    # Latest visit: still on pump, but closed_loop_system not recorded this time
    VisitFactory(
        patient=patient,
        visit_date=visit_date + relativedelta(days=90),
        treatment=3,
        closed_loop_system=None,
    )

    submission = _create_submission(user, pdu, audit_period)
    submission.patients.add(patient)

    passed, eligible = count_hcl_use(pdu, audit_period)

    assert eligible == 1
    assert passed == 0  # closed_loop_system is null on the latest treatment visit


@pytest.mark.django_db
def test_count_hcl_use_2026_reverted_patient_excluded_from_total(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    """
    2026 dataset regression: a patient whose earlier visit had insulin_regimen=5
    (HCL) but whose most recent insulin_regimen visit is a standalone pump (4)
    must NOT be counted in the HCL total.
    """
    user, pdu = _get_user_and_pdu()
    audit_period = AuditPeriod.objects.get(slug="2026-2027")
    visit_date = audit_period.start_date + relativedelta(days=10)

    still_on_hcl = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )
    reverted_to_pump = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )

    # still_on_hcl: single visit, insulin_regimen=5
    VisitFactory(
        patient=still_on_hcl,
        visit_date=visit_date,
        treatment=None,
        closed_loop_system=None,
        glucose_monitoring=None,
        insulin_regimen=5,  # Hybrid closed loop
    )

    # reverted_to_pump: first visit was HCL, latest is standalone pump
    VisitFactory(
        patient=reverted_to_pump,
        visit_date=visit_date,
        treatment=None,
        closed_loop_system=None,
        glucose_monitoring=None,
        insulin_regimen=5,  # Hybrid closed loop
    )
    VisitFactory(
        patient=reverted_to_pump,
        visit_date=visit_date + relativedelta(days=90),
        treatment=None,
        closed_loop_system=None,
        glucose_monitoring=None,
        insulin_regimen=4,  # Standalone pump — no longer HCL
    )

    submission = _create_submission(user, pdu, audit_period)
    submission.patients.add(still_on_hcl, reverted_to_pump)

    passed, eligible = count_hcl_use(pdu, audit_period)

    assert eligible == 2
    assert passed == 1  # only still_on_hcl passes


# ---------------------------------------------------------------------------
# count_pump_use — 2021 dataset
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_count_pump_use_2021_treatment_3_or_6_is_passed(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    """2021 dataset: treatment=3 (pump) or treatment=6 (pump + other) → passed."""
    user, pdu = _get_user_and_pdu()
    audit_period = AuditPeriod.objects.get(slug="2024-2025")
    visit_date = audit_period.start_date + relativedelta(days=10)

    pump = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )
    pump_plus_other = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )
    injections = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )
    VisitFactory(patient=pump, visit_date=visit_date, treatment=3)
    VisitFactory(patient=pump_plus_other, visit_date=visit_date, treatment=6)
    VisitFactory(patient=injections, visit_date=visit_date, treatment=2)

    submission = _create_submission(user, pdu, audit_period)
    submission.patients.add(pump, pump_plus_other, injections)

    passed, eligible = count_pump_use(pdu, audit_period)

    assert passed == 2
    assert eligible == 3


# ---------------------------------------------------------------------------
# count_pump_use — 2026 dataset
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_count_pump_use_2026_insulin_regimen_4_or_5_is_passed(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    """2026 dataset: insulin_regimen=4 (standalone pump) or 5 (HCL, which uses pump) → passed."""
    user, pdu = _get_user_and_pdu()
    audit_period = AuditPeriod.objects.get(slug="2026-2027")
    visit_date = audit_period.start_date + relativedelta(days=10)

    pump_standalone = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )
    hcl = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )
    injections = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )
    VisitFactory(
        patient=pump_standalone,
        visit_date=visit_date,
        treatment=None,
        closed_loop_system=None,
        glucose_monitoring=None,
        insulin_regimen=4,
    )
    VisitFactory(
        patient=hcl,
        visit_date=visit_date,
        treatment=None,
        closed_loop_system=None,
        glucose_monitoring=None,
        insulin_regimen=5,
    )
    VisitFactory(
        patient=injections,
        visit_date=visit_date,
        treatment=None,
        closed_loop_system=None,
        glucose_monitoring=None,
        insulin_regimen=3,  # four+ injections/day
    )

    submission = _create_submission(user, pdu, audit_period)
    submission.patients.add(pump_standalone, hcl, injections)

    passed, eligible = count_pump_use(pdu, audit_period)

    assert passed == 2
    assert eligible == 3


# ---------------------------------------------------------------------------
# count_cgm_use — 2021 dataset
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_count_cgm_use_2021_glucose_monitoring_4_is_passed(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    """2021 dataset: glucose_monitoring=4 (real-time CGM with alarms) → passed."""
    user, pdu = _get_user_and_pdu()
    audit_period = AuditPeriod.objects.get(slug="2024-2025")
    visit_date = audit_period.start_date + relativedelta(days=10)

    on_rtcgm = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )
    on_flash = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )
    VisitFactory(
        patient=on_rtcgm,
        visit_date=visit_date,
        glucose_monitoring=GLUCOSE_MONITORING_TYPES[3][
            0
        ],  # 4 = real-time CGM with alarms
    )
    VisitFactory(
        patient=on_flash,
        visit_date=visit_date,
        glucose_monitoring=GLUCOSE_MONITORING_TYPES[1][0],  # 2 = flash
    )

    submission = _create_submission(user, pdu, audit_period)
    submission.patients.add(on_rtcgm, on_flash)

    passed, eligible = count_cgm_use(pdu, audit_period)

    assert passed == 1
    assert eligible == 2


# ---------------------------------------------------------------------------
# count_cgm_use — 2026 dataset
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_count_cgm_use_2026_cgm_use_yes_is_passed(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    """2026 dataset: cgm_use=1 (Yes) → passed; cgm_use=2 (No) → not passed."""
    user, pdu = _get_user_and_pdu()
    audit_period = AuditPeriod.objects.get(slug="2026-2027")
    visit_date = audit_period.start_date + relativedelta(days=10)

    using_cgm = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )
    not_using_cgm = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )
    VisitFactory(
        patient=using_cgm,
        visit_date=visit_date,
        treatment=None,
        closed_loop_system=None,
        glucose_monitoring=None,
        cgm_use=1,  # Yes
    )
    VisitFactory(
        patient=not_using_cgm,
        visit_date=visit_date,
        treatment=None,
        closed_loop_system=None,
        glucose_monitoring=None,
        cgm_use=2,  # No
    )

    submission = _create_submission(user, pdu, audit_period)
    submission.patients.add(using_cgm, not_using_cgm)

    passed, eligible = count_cgm_use(pdu, audit_period)

    assert passed == 1
    assert eligible == 2


# ---------------------------------------------------------------------------
# count_admissions
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_count_admissions_counts_patients_with_valid_admission_in_audit_period(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    """Patients with a valid hospital admission within the audit period are counted."""
    user, pdu = _get_user_and_pdu()
    audit_period = AuditPeriod.objects.get(slug="2024-2025")
    visit_date = audit_period.start_date + relativedelta(days=10)
    admission_date = audit_period.start_date + relativedelta(days=30)

    admitted = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        diagnosis_date=audit_period.start_date - relativedelta(days=91),
    )
    not_admitted = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        diagnosis_date=audit_period.start_date - relativedelta(days=91),
    )
    VisitFactory(
        patient=admitted,
        visit_date=visit_date,
        hospital_admission_date=admission_date,
        hospital_discharge_date=admission_date + relativedelta(days=2),
        hospital_admission_reason=HOSPITAL_ADMISSION_REASONS[0][0],
    )
    VisitFactory(
        patient=not_admitted,
        visit_date=visit_date,
        hospital_admission_date=None,
    )

    submission = _create_submission(user, pdu, audit_period)
    submission.patients.add(admitted, not_admitted)

    assert count_admissions(pdu, audit_period) == 1


@pytest.mark.django_db
def test_count_admissions_includes_admission_within_90_days_of_diagnosis(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    """Admissions within 90 days of diagnosis ARE counted.

    count_admissions mirrors KPI 46, which does not apply the 90-day exclusion
    used in the patient-report's annotate_admissions(). That exclusion is
    intentional only for the patient-report row-level view.
    """
    user, pdu = _get_user_and_pdu()
    audit_period = AuditPeriod.objects.get(slug="2024-2025")
    visit_date = audit_period.start_date + relativedelta(days=10)

    newly_diagnosed = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        # Diagnosed only 30 days before the admission
        diagnosis_date=audit_period.start_date + relativedelta(days=5),
    )
    VisitFactory(
        patient=newly_diagnosed,
        visit_date=visit_date,
        hospital_admission_date=audit_period.start_date + relativedelta(days=35),
        hospital_discharge_date=audit_period.start_date + relativedelta(days=37),
        hospital_admission_reason=HOSPITAL_ADMISSION_REASONS[1][0],  # DKA
    )

    submission = _create_submission(user, pdu, audit_period)
    submission.patients.add(newly_diagnosed)

    # KPI 46 counts this — no 90-day exclusion
    assert count_admissions(pdu, audit_period) == 1


# ---------------------------------------------------------------------------
# dashboard_health_check_totals
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_dashboard_health_check_totals_under_12_not_eligible_for_age_gated_checks(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    """Patients under 12 at audit start are not eligible for BP, ACR, or foot exam."""
    user, pdu = _get_user_and_pdu()
    audit_period = AuditPeriod.objects.get(slug="2024-2025")
    visit_date = audit_period.start_date + relativedelta(days=10)

    # Patient aged 11 at audit start — under 12
    patient = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=11, days=2),
        diagnosis_date=audit_period.start_date - relativedelta(days=2),
    )
    VisitFactory(
        patient=patient,
        visit_date=visit_date,
        systolic_blood_pressure=110,
        blood_pressure_observation_date=visit_date,
        albumin_creatinine_ratio=1.2,
        albumin_creatinine_ratio_date=visit_date,
        foot_examination_observation_date=visit_date,
    )

    submission = _create_submission(user, pdu, audit_period)
    submission.patients.add(patient)

    totals = dashboard_health_check_totals(pdu, audit_period)

    assert totals["total_eligible_blood_pressure"] == 0
    assert totals["total_eligible_urinary_albumin"] == 0
    assert totals["total_eligible_foot_exam"] == 0


@pytest.mark.django_db
def test_dashboard_health_check_totals_over_12_with_bp_is_passed(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    """A patient over 12 at audit start with a BP measurement in the audit year is passed."""
    user, pdu = _get_user_and_pdu()
    audit_period = AuditPeriod.objects.get(slug="2024-2025")
    visit_date = audit_period.start_date + relativedelta(days=10)

    # Aged 13 at audit start (complete year of care: diagnosed before audit start)
    patient = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=13),
        diagnosis_date=audit_period.start_date - relativedelta(days=2),
    )
    VisitFactory(
        patient=patient,
        visit_date=visit_date,
        systolic_blood_pressure=110,
        blood_pressure_observation_date=visit_date,
    )

    submission = _create_submission(user, pdu, audit_period)
    submission.patients.add(patient)

    totals = dashboard_health_check_totals(pdu, audit_period)

    assert totals["total_eligible_blood_pressure"] == 1
    assert totals["total_passed_blood_pressure"] == 1


@pytest.mark.django_db
def test_dashboard_health_check_totals_2026_dataset(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture
):
    """Health check totals work identically for the 2026 dataset (same model fields)."""
    user, pdu = _get_user_and_pdu()
    audit_period = AuditPeriod.objects.get(slug="2026-2027")
    visit_date = audit_period.start_date + relativedelta(days=10)

    patient = PatientFactory(
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=audit_period.start_date - relativedelta(years=13),
        diagnosis_date=audit_period.start_date - relativedelta(days=2),
    )
    VisitFactory(
        patient=patient,
        visit_date=visit_date,
        treatment=None,
        closed_loop_system=None,
        glucose_monitoring=None,
        systolic_blood_pressure=110,
        blood_pressure_observation_date=visit_date,
    )

    submission = _create_submission(user, pdu, audit_period)
    submission.patients.add(patient)

    totals = dashboard_health_check_totals(pdu, audit_period)

    assert totals["total_eligible_blood_pressure"] == 1
    assert totals["total_passed_blood_pressure"] == 1
