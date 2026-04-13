"""Tests for the patient measurements dashboard view."""

from http import HTTPStatus

# Python imports
import pytest
from dateutil.relativedelta import relativedelta

# 3rd party imports
from django.urls import reverse

from project.constants.diabetes_types import DIABETES_TYPES

# E12 imports
from project.npda.models import NPDAUser
from project.npda.models.audit_period import AuditPeriod
from project.npda.models.submission import Submission
from project.npda.tests.constants_for_tests import ALDER_HEY_PZ_CODE
from project.npda.tests.factories import test_user_audit_centre_editor_data
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.factories.visit_factory import VisitFactory
from project.npda.tests.utils import login_and_verify_user


def _get_user(pz_code=ALDER_HEY_PZ_CODE):
    return NPDAUser.objects.filter(
        organisation_employers__pz_code=pz_code,
        role=test_user_audit_centre_editor_data.role,
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


def _url(audit_period):
    return reverse(
        "pdu-patient-measurements",
        kwargs={"audit_period": audit_period.slug, "pz_code": ALDER_HEY_PZ_CODE},
    )


# ---------------------------------------------------------------------------
# 2021 dataset (audit period 2024-2025)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_measurements_under_12_not_eligible_for_age_gated_checks_2021(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture, client
):
    """
    2021 dataset: a patient who is under 12 at the audit start date is not eligible
    for blood pressure, urinary albumin, or foot examination checks.

    Uses the 2024-2025 audit period (dataset year 2021).
    """
    user = _get_user()
    client = login_and_verify_user(client, user)

    audit_period = AuditPeriod.objects.get(slug="2024-2025")

    patient = PatientFactory(
        nhs_number="4444444444",
        diabetes_type=DIABETES_TYPES[0][0],  # T1DM
        date_of_birth=audit_period.start_date - relativedelta(years=11, days=2),
        diagnosis_date=audit_period.start_date - relativedelta(days=2),
    )
    VisitFactory(
        patient=patient,
        visit_date=audit_period.start_date + relativedelta(days=10),
        hba1c=60,
        hba1c_date=audit_period.start_date + relativedelta(days=10),
        # hba1c_format uses VisitFactory default (mmol/mol) — correct for 2021
    )

    submission = _create_submission(user, audit_period)
    submission.patients.add(patient)

    response = client.get(_url(audit_period))

    assert response.status_code == HTTPStatus.OK
    assert response.context["total_eligible_blood_pressure"] == 0
    assert response.context["total_eligible_urinary_albumin"] == 0
    assert response.context["total_eligible_foot_exam"] == 0


# ---------------------------------------------------------------------------
# 2026 dataset (audit period 2026-2027)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_measurements_under_12_not_eligible_for_age_gated_checks_2026(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture, client
):
    """
    2026 dataset: same age-gate logic applies — patient under 12 is not eligible
    for blood pressure, urinary albumin, or foot examination checks.

    Uses the 2026-2027 audit period (dataset year 2026).
    hba1c_format is omitted — it is a 2021-only field; format is inferred in 2026.
    """
    user = _get_user()
    client = login_and_verify_user(client, user)

    audit_period = AuditPeriod.objects.get(slug="2026-2027")

    patient = PatientFactory(
        nhs_number="5555555555",
        diabetes_type=DIABETES_TYPES[0][0],  # T1DM
        date_of_birth=audit_period.start_date - relativedelta(years=11, days=2),
        diagnosis_date=audit_period.start_date - relativedelta(days=2),
    )
    VisitFactory(
        patient=patient,
        visit_date=audit_period.start_date + relativedelta(days=10),
        hba1c=60,
        hba1c_date=audit_period.start_date + relativedelta(days=10),
        # 2026 fields — override 2021-specific VisitFactory defaults to None
        treatment=None,
        closed_loop_system=None,
        glucose_monitoring=None,
    )

    submission = _create_submission(user, audit_period)
    submission.patients.add(patient)

    response = client.get(_url(audit_period))

    assert response.status_code == HTTPStatus.OK
    assert response.context["total_eligible_blood_pressure"] == 0
    assert response.context["total_eligible_urinary_albumin"] == 0
    assert response.context["total_eligible_foot_exam"] == 0
