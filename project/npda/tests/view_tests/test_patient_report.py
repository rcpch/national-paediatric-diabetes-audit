"""Tests for the patient report view"""

import logging
from decimal import Decimal
from http import HTTPStatus

import pytest
from dateutil.relativedelta import relativedelta

# 3rd party imports
from django.urls import reverse

from project.constants.closed_loop_types import CLOSED_LOOP_TYPES
from project.constants.diabetes_treatment import INSULIN_TREATMENT, TREATMENT_TYPES
from project.constants.diabetes_types import DIABETES_TYPES
from project.constants.glucose_monitoring_types import GLUCOSE_MONITORING_TYPES
from project.constants.hba1c_format import HBA1C_FORMATS

# Python imports
from project.constants.smoking_status import SMOKING_STATUS, SMOKING_VAPING_STATUS
from project.constants.yes_no_unknown import YES_NO_UNKNOWN
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
from project.npda.models.transfer import Transfer
from project.npda.tests.constants_for_tests import ALDER_HEY_PZ_CODE
from project.npda.tests.factories import (
    test_user_audit_centre_editor_data,
    test_user_rcpch_audit_team_data,
)
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.factories.transfer_factory import TransferFactory
from project.npda.tests.factories.visit_factory import VisitFactory
from project.npda.tests.utils import login_and_verify_user
from project.npda.urls import patient_report_urlpatterns
from project.npda.views.patient_report.patient_report import TableCategories

logger = logging.getLogger(__name__)


@pytest.mark.django_db
def test_anonymous_user_cannot_access_patient_report(
    client,
):
    """Anonymous users should not be able to access the patient report."""

    for url in patient_report_urlpatterns:
        if url.name.startswith("pdu-"):
            resolved_url = reverse(
                url.name,
                kwargs={"audit_period": "2023-2024", "pz_code": ALDER_HEY_PZ_CODE},
            )
        else:
            resolved_url = reverse(url.name)

        response = client.get(resolved_url)

        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("login") + "?next=" + resolved_url


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
        audit_period=audit_period,
        submission_date=audit_period.start_date,
        submission_by=ah_rcpch_audit_team_user,
        submission_active=True,
    )

    # Add patients to submission
    new_submission.patients.add(*new_pts)

    # Get the patient report
    response = client.get(
        reverse(
            "pdu-patient-report",
            kwargs={"audit_period": audit_period.slug, "pz_code": ALDER_HEY_PZ_CODE},
        )
    )
    assert response.status_code == HTTPStatus.OK

    assert isinstance(response.context["patients"], list)
    assert len(response.context["patients"]) == N_PATIENTS

    # Check that there are no duplicate patients
    duplicates = {
        patient["patient_identifier"] for patient in response.context["patients"]
    }
    assert len(duplicates) == N_PATIENTS


@pytest.mark.django_db
def _create_outcomes_test_setup(client, audit_period_slug=None):
    """Helper function to create common test setup for outcomes tests."""
    # Login as RCPCH Audit Team user
    ah_rcpch_audit_team_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_rcpch_audit_team_data.role,
    ).first()
    client = login_and_verify_user(client, ah_rcpch_audit_team_user)

    # Get audit period and ensure it's open
    if audit_period_slug is not None:
        audit_period = AuditPeriod.objects.get(slug=audit_period_slug)
    else:
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

    return ah_rcpch_audit_team_user, audit_period, AUDIT_START_DATE, eligible_criteria


@pytest.mark.parametrize("audit_period_slug", ["2024-2025", "2026-2027"])
@pytest.mark.django_db
def test_outcomes_no_hba1c_measurements(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    audit_period_slug,
):
    """
    Test outcomes view for patient with no HbA1c measurements.

    Verifies that all HbA1c-related fields are None when a patient
    has visits but no HbA1c data recorded.
    """
    ah_rcpch_audit_team_user, audit_period, AUDIT_START_DATE, eligible_criteria = (
        _create_outcomes_test_setup(client, audit_period_slug)
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
        audit_period=audit_period,
        submission_date=AUDIT_START_DATE,
        submission_by=ah_rcpch_audit_team_user,
        submission_active=True,
    )
    submission.patients.add(patient)

    url = reverse(
        "pdu-patient-report",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )

    # Get the patient report with outcomes category
    response = client.get(
        url + f"?category={TableCategories.OUTCOMES.value}",
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


@pytest.mark.parametrize(
    "audit_period_slug, hba1c_format_val",
    [
        ("2024-2025", HBA1C_FORMATS[0][0]),
        ("2026-2027", None),  # 2026: hba1c_format deprecated, values always mmol/mol
    ],
)
@pytest.mark.django_db
def test_outcomes_single_hba1c_measurement(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    audit_period_slug,
    hba1c_format_val,
):
    """
    Test outcomes view for patient with single HbA1c measurement.

    Verifies that latest HbA1c values are populated correctly while
    previous values remain None, and no delta calculations are performed.
    """
    ah_rcpch_audit_team_user, audit_period, AUDIT_START_DATE, eligible_criteria = (
        _create_outcomes_test_setup(client, audit_period_slug)
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
        hba1c_format=hba1c_format_val,
        hba1c_date=AUDIT_START_DATE + relativedelta(days=5),
    )

    # Create submission
    submission = Submission.objects.create(
        paediatric_diabetes_unit=ah_rcpch_audit_team_user.organisation_employers.first(),
        audit_year=AUDIT_START_DATE.year,
        audit_period=audit_period,
        submission_date=AUDIT_START_DATE,
        submission_by=ah_rcpch_audit_team_user,
        submission_active=True,
    )
    submission.patients.add(patient)

    url = reverse(
        "pdu-patient-report",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )

    # Get the patient report with outcomes category
    response = client.get(
        url + f"?category={TableCategories.OUTCOMES.value}",
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


@pytest.mark.parametrize(
    "audit_period_slug, hba1c_format_val",
    [
        ("2024-2025", HBA1C_FORMATS[0][0]),
        ("2026-2027", None),  # 2026: hba1c_format deprecated, values always mmol/mol
    ],
)
@pytest.mark.django_db
def test_outcomes_multiple_hba1c_measurements(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    audit_period_slug,
    hba1c_format_val,
):
    """
    Test outcomes view for patient with multiple HbA1c measurements.

    Verifies that both latest and previous HbA1c values are populated correctly,
    percentage conversions are accurate, and delta calculations show the
    percentage change between measurements.
    """
    ah_rcpch_audit_team_user, audit_period, AUDIT_START_DATE, eligible_criteria = (
        _create_outcomes_test_setup(client, audit_period_slug)
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
        hba1c_format=hba1c_format_val,
        hba1c_date=AUDIT_START_DATE + relativedelta(days=10),
    )
    # Latest hba1c
    VisitFactory(
        patient=patient,
        visit_date=AUDIT_START_DATE + relativedelta(days=20),
        hba1c=45,  # 45 mmol/mol
        hba1c_format=hba1c_format_val,
        hba1c_date=AUDIT_START_DATE + relativedelta(days=20),
    )

    # Create submission
    submission = Submission.objects.create(
        paediatric_diabetes_unit=ah_rcpch_audit_team_user.organisation_employers.first(),
        audit_year=AUDIT_START_DATE.year,
        audit_period=audit_period,
        submission_date=AUDIT_START_DATE,
        submission_by=ah_rcpch_audit_team_user,
        submission_active=True,
    )
    submission.patients.add(patient)

    url = reverse(
        "pdu-patient-report",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )

    # Get the patient report with outcomes category
    response = client.get(
        url + f"?category={TableCategories.OUTCOMES.value}",
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


@pytest.mark.parametrize("audit_period_slug", ["2024-2025", "2026-2027"])
@pytest.mark.django_db
def test_report_for_patients_turning_12_in_audit_year(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    audit_period_slug,
):
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()

    client = login_and_verify_user(client, user)

    audit_period = AuditPeriod.objects.get(slug=audit_period_slug)
    audit_period.is_open = True
    audit_period.save()

    date_of_birth = audit_period.start_date - relativedelta(years=11, days=2)

    patient = PatientFactory(
        nhs_number="4444444444",
        diabetes_type=DIABETES_TYPES[0][0],  # T1DM
        date_of_birth=date_of_birth,
        diagnosis_date=audit_period.start_date
        - relativedelta(days=2),  # complete year of care
    )

    # Need a visit in the audit period to be eligible
    VisitFactory(
        patient=patient,
        visit_date=audit_period.start_date + relativedelta(days=10),
        hba1c=60,  # 60 mmol/mol
        hba1c_format=HBA1C_FORMATS[0][0],  # mmol/mol format
        hba1c_date=audit_period.start_date + relativedelta(days=10),
    )

    submission = Submission.objects.create(
        paediatric_diabetes_unit=user.organisation_employers.first(),
        audit_year=audit_period.start_date.year,
        audit_period=audit_period,
        submission_date=audit_period.start_date,
        submission_by=user,
        submission_active=True,
    )
    submission.patients.add(patient)

    url = reverse(
        "pdu-patient-report",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )

    response = client.get(
        url + f"?category={TableCategories.HEALTH_CHECKS.value}",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == HTTPStatus.OK

    assert len(response.context["patients"]) == 1

    patient = response.context["patients"][0]

    assert patient["patient_identifier"] == "4444444444"
    assert patient["passed_blood_pressure"] is None
    assert patient["passed_urinary_albumin"] is None
    assert patient["passed_foot_exam"] is None

    assert response.context["total_eligible_blood_pressure"] == 0
    assert response.context["total_eligible_urinary_albumin"] == 0
    assert response.context["total_eligible_foot_exam"] == 0

    url = reverse(
        "pdu-patient-report",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )

    response = client.get(
        url + f"?category={TableCategories.ADDITIONAL_CARE_PROCESSES.value}",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == HTTPStatus.OK

    assert len(response.context["patients"]) == 1

    patient = response.context["patients"][0]

    assert patient["patient_identifier"] == "4444444444"
    assert patient["smoking_status"] is None
    assert patient["smoking_cessation_referral"] == "under_12"


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/1197
@pytest.mark.parametrize("audit_period_slug", ["2024-2025", "2026-2027"])
@pytest.mark.django_db
def test_report_for_sick_day_rules(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    audit_period_slug,
):
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()

    client = login_and_verify_user(client, user)

    audit_period = AuditPeriod.objects.get(slug=audit_period_slug)
    audit_period.is_open = True
    audit_period.save()

    date_of_birth = audit_period.start_date - relativedelta(years=14)

    patient = PatientFactory(
        nhs_number="4444444444",
        diabetes_type=DIABETES_TYPES[0][0],  # T1DM
        date_of_birth=date_of_birth,
        diagnosis_date=audit_period.start_date
        - relativedelta(days=2),  # complete year of care
    )

    visit_date = audit_period.start_date + relativedelta(days=10)

    VisitFactory(
        patient=patient,
        visit_date=visit_date,
        sick_day_rules_training_date=visit_date,
    )

    submission = Submission.objects.create(
        paediatric_diabetes_unit=user.organisation_employers.first(),
        audit_year=audit_period.start_date.year,
        audit_period=audit_period,
        submission_date=audit_period.start_date,
        submission_by=user,
        submission_active=True,
    )
    submission.patients.add(patient)

    url = reverse(
        "pdu-patient-report",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )

    response = client.get(
        url + f"?category={TableCategories.ADDITIONAL_CARE_PROCESSES.value}",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == HTTPStatus.OK

    assert len(response.context["patients"]) == 1

    patient = response.context["patients"][0]

    assert patient["patient_identifier"] == "4444444444"
    assert patient["sick_day_rules_advice"]


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/1199
@pytest.mark.parametrize("audit_period_slug", ["2024-2025", "2026-2027"])
@pytest.mark.django_db
def test_care_at_diagnosis_for_type_1_patient(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    audit_period_slug,
):
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()

    client = login_and_verify_user(client, user)

    audit_period = AuditPeriod.objects.get(slug=audit_period_slug)
    audit_period.is_open = True
    audit_period.save()

    date_of_birth = audit_period.start_date - relativedelta(years=14)

    patient = PatientFactory(
        nhs_number="4444444444",
        diabetes_type=DIABETES_TYPES[0][0],  # T1DM
        date_of_birth=date_of_birth,
        diagnosis_date=audit_period.start_date
        + relativedelta(days=2),  # diagnosed within the audit year
    )

    visit_date = audit_period.start_date + relativedelta(days=10)

    VisitFactory(
        patient=patient,
        visit_date=visit_date,
        carbohydrate_counting_level_three_education_date=visit_date,
    )

    submission = Submission.objects.create(
        paediatric_diabetes_unit=user.organisation_employers.first(),
        audit_year=audit_period.start_date.year,
        audit_period=audit_period,
        submission_date=audit_period.start_date,
        submission_by=user,
        submission_active=True,
    )
    submission.patients.add(patient)

    url = reverse(
        "pdu-patient-report",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )

    response = client.get(
        url + f"?category={TableCategories.CARE_AT_DIAGNOSIS.value}",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == HTTPStatus.OK

    assert len(response.context["patients"]) == 1

    patient = response.context["patients"][0]

    assert patient["patient_identifier"] == "4444444444"
    assert patient["carbohydrate_counting_education"]
    assert patient["carb_counting_status"] == "on_time"

    # Not completed yet
    assert not patient["coeliac_disease_screening"]
    assert not patient["thyroid_disease_screening"]


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/1301
@pytest.mark.parametrize("audit_period_slug", ["2024-2025", "2026-2027"])
@pytest.mark.django_db
def test_carb_counting_countdown_when_no_date_entered(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    audit_period_slug,
):
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()

    client = login_and_verify_user(client, user)

    audit_period = AuditPeriod.objects.get(slug=audit_period_slug)
    audit_period.is_open = True
    audit_period.save()

    reference_date = audit_period.kpi_calculation_date()
    diagnosis_date = reference_date - relativedelta(days=7)

    patient = PatientFactory(
        nhs_number="9999990000",
        diabetes_type=DIABETES_TYPES[0][0],  # T1DM
        date_of_birth=reference_date - relativedelta(years=14),
        diagnosis_date=diagnosis_date,
    )

    VisitFactory(
        patient=patient,
        visit_date=reference_date - relativedelta(days=1),
    )

    submission = Submission.objects.create(
        paediatric_diabetes_unit=user.organisation_employers.first(),
        audit_year=audit_period.start_date.year,
        audit_period=audit_period,
        submission_date=audit_period.start_date,
        submission_by=user,
        submission_active=True,
    )
    submission.patients.add(patient)

    url = reverse(
        "pdu-patient-report",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )

    response = client.get(
        url + f"?category={TableCategories.CARE_AT_DIAGNOSIS.value}",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == HTTPStatus.OK

    assert len(response.context["patients"]) == 1

    patient = response.context["patients"][0]

    assert patient["carb_counting_status"] == "countdown"
    assert patient["carb_counting_countdown_label"] == "Due in 7 days"


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/1301
# Note: uses 2025-2026 (not 2026-2027) as the second period — these tests derive
# diagnosis_date from kpi_calculation_date() - N days, so they only work when the
# period has been running for at least N days. 2025-2026 is always a completed period.
@pytest.mark.parametrize("audit_period_slug", ["2024-2025", "2025-2026"])
@pytest.mark.django_db
def test_coeliac_screening_countdown_when_no_date_entered(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    audit_period_slug,
):
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()

    client = login_and_verify_user(client, user)

    audit_period = AuditPeriod.objects.get(slug=audit_period_slug)
    audit_period.is_open = True
    audit_period.save()

    reference_date = audit_period.kpi_calculation_date()
    diagnosis_date = reference_date - relativedelta(days=20)

    patient = PatientFactory(
        nhs_number="9999990001",
        diabetes_type=DIABETES_TYPES[0][0],  # T1DM
        date_of_birth=reference_date - relativedelta(years=14),
        diagnosis_date=diagnosis_date,
    )

    VisitFactory(
        patient=patient,
        visit_date=reference_date - relativedelta(days=1),
    )

    submission = Submission.objects.create(
        paediatric_diabetes_unit=user.organisation_employers.first(),
        audit_year=audit_period.start_date.year,
        audit_period=audit_period,
        submission_date=audit_period.start_date,
        submission_by=user,
        submission_active=True,
    )
    submission.patients.add(patient)

    url = reverse(
        "pdu-patient-report",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )

    response = client.get(
        url + f"?category={TableCategories.CARE_AT_DIAGNOSIS.value}",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == HTTPStatus.OK

    assert len(response.context["patients"]) == 1

    patient = response.context["patients"][0]

    assert patient["coeliac_screening_status"] == "countdown"
    assert patient["coeliac_screening_countdown_label"] == "Due in 70 days"


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/1301
# Note: uses 2025-2026 (not 2026-2027) — same reason as test_coeliac_screening_countdown.
@pytest.mark.parametrize("audit_period_slug", ["2024-2025", "2025-2026"])
@pytest.mark.django_db
def test_thyroid_screening_overdue_when_threshold_passed(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    audit_period_slug,
):
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()

    client = login_and_verify_user(client, user)

    audit_period = AuditPeriod.objects.get(slug=audit_period_slug)
    audit_period.is_open = True
    audit_period.save()

    reference_date = audit_period.kpi_calculation_date()
    diagnosis_date = reference_date - relativedelta(days=100)

    patient = PatientFactory(
        nhs_number="9999990002",
        diabetes_type=DIABETES_TYPES[0][0],  # T1DM
        date_of_birth=reference_date - relativedelta(years=14),
        diagnosis_date=diagnosis_date,
    )

    VisitFactory(
        patient=patient,
        visit_date=reference_date - relativedelta(days=1),
    )

    submission = Submission.objects.create(
        paediatric_diabetes_unit=user.organisation_employers.first(),
        audit_year=audit_period.start_date.year,
        audit_period=audit_period,
        submission_date=audit_period.start_date,
        submission_by=user,
        submission_active=True,
    )
    submission.patients.add(patient)

    url = reverse(
        "pdu-patient-report",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )

    response = client.get(
        url + f"?category={TableCategories.CARE_AT_DIAGNOSIS.value}",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == HTTPStatus.OK

    assert len(response.context["patients"]) == 1

    patient = response.context["patients"][0]

    assert patient["thyroid_screening_status"] == "overdue"


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/1301
@pytest.mark.parametrize("audit_period_slug", ["2024-2025", "2026-2027"])
@pytest.mark.django_db
def test_coeliac_and_thyroid_screening_on_time_when_dates_present(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    audit_period_slug,
):
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()

    client = login_and_verify_user(client, user)

    audit_period = AuditPeriod.objects.get(slug=audit_period_slug)
    audit_period.is_open = True
    audit_period.save()

    diagnosis_date = audit_period.start_date + relativedelta(days=2)
    visit_date = diagnosis_date + relativedelta(days=30)

    patient = PatientFactory(
        nhs_number="9999990003",
        diabetes_type=DIABETES_TYPES[0][0],  # T1DM
        date_of_birth=audit_period.start_date - relativedelta(years=14),
        diagnosis_date=diagnosis_date,
    )

    VisitFactory(
        patient=patient,
        visit_date=visit_date,
        coeliac_screen_date=visit_date,
        thyroid_function_date=visit_date,
    )

    submission = Submission.objects.create(
        paediatric_diabetes_unit=user.organisation_employers.first(),
        audit_year=audit_period.start_date.year,
        audit_period=audit_period,
        submission_date=audit_period.start_date,
        submission_by=user,
        submission_active=True,
    )
    submission.patients.add(patient)

    url = reverse(
        "pdu-patient-report",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )

    response = client.get(
        url + f"?category={TableCategories.CARE_AT_DIAGNOSIS.value}",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == HTTPStatus.OK

    assert len(response.context["patients"]) == 1

    patient = response.context["patients"][0]

    assert patient["coeliac_screening_status"] == "on_time"
    assert patient["thyroid_screening_status"] == "on_time"


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/1199
@pytest.mark.parametrize("audit_period_slug", ["2024-2025", "2026-2027"])
@pytest.mark.django_db
def test_non_type_1_patients_do_not_appear_in_care_at_diagnosis(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    audit_period_slug,
):
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()

    client = login_and_verify_user(client, user)

    audit_period = AuditPeriod.objects.get(slug=audit_period_slug)
    audit_period.is_open = True
    audit_period.save()

    date_of_birth = audit_period.start_date - relativedelta(years=14)

    patient = PatientFactory(
        nhs_number="4444444444",
        diabetes_type=DIABETES_TYPES[1][0],  # T2DM
        date_of_birth=date_of_birth,
        diagnosis_date=audit_period.start_date
        + relativedelta(days=2),  # diagnosed within the audit year
    )

    visit_date = audit_period.start_date + relativedelta(days=10)

    VisitFactory(
        patient=patient,
        visit_date=visit_date,
        carbohydrate_counting_level_three_education_date=visit_date,
    )

    submission = Submission.objects.create(
        paediatric_diabetes_unit=user.organisation_employers.first(),
        audit_year=audit_period.start_date.year,
        audit_period=audit_period,
        submission_date=audit_period.start_date,
        submission_by=user,
        submission_active=True,
    )
    submission.patients.add(patient)

    url = reverse(
        "pdu-patient-report",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )

    response = client.get(
        url + f"?category={TableCategories.CARE_AT_DIAGNOSIS.value}",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == HTTPStatus.OK

    assert len(response.context["patients"]) == 0


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/1242
@pytest.mark.parametrize("audit_period_slug", ["2024-2025", "2026-2027"])
@pytest.mark.django_db
def test_patient_with_incomplete_year_of_care_can_still_show_as_passing_hba1c_healthcheck(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    audit_period_slug,
):
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()

    client = login_and_verify_user(client, user)

    audit_period = AuditPeriod.objects.get(slug=audit_period_slug)
    audit_period.is_open = True
    audit_period.save()

    date_of_birth = audit_period.start_date - relativedelta(years=14)

    patient = PatientFactory(
        nhs_number="4444444444",
        diabetes_type=DIABETES_TYPES[0][0],  # T1DM
        date_of_birth=date_of_birth,
        diagnosis_date=audit_period.start_date
        + relativedelta(days=2),  # diagnosed within the audit year
    )

    visit_date = audit_period.start_date + relativedelta(days=10)

    VisitFactory(
        patient=patient,
        visit_date=visit_date,
        hba1c=50,  # 50 mmol/mol
        hba1c_format=HBA1C_FORMATS[0][0],  # mmol/mol format
        hba1c_date=visit_date,
    )

    submission = Submission.objects.create(
        paediatric_diabetes_unit=user.organisation_employers.first(),
        audit_year=audit_period.start_date.year,
        audit_period=audit_period,
        submission_date=audit_period.start_date,
        submission_by=user,
        submission_active=True,
    )
    submission.patients.add(patient)

    url = reverse(
        "pdu-patient-report",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )

    response = client.get(
        url + f"?category={TableCategories.HEALTH_CHECKS.value}",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == HTTPStatus.OK

    assert len(response.context["patients"]) == 1

    patient = response.context["patients"][0]

    assert patient["patient_identifier"] == "4444444444"
    assert patient["passed_hba1c"] is True


# https://github.com/rcpch/national-paediatric-diabetes-audit/issues/1242
@pytest.mark.parametrize("audit_period_slug", ["2024-2025", "2026-2027"])
@pytest.mark.django_db
def test_patient_with_incomplete_year_of_care_can_still_show_as_passing_influenza_immunisation_recommended(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    audit_period_slug,
):
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()

    client = login_and_verify_user(client, user)

    audit_period = AuditPeriod.objects.get(slug=audit_period_slug)
    audit_period.is_open = True
    audit_period.save()

    date_of_birth = audit_period.start_date - relativedelta(years=14)

    patient = PatientFactory(
        nhs_number="4444444444",
        diabetes_type=DIABETES_TYPES[0][0],  # T1DM
        date_of_birth=date_of_birth,
        diagnosis_date=audit_period.start_date
        + relativedelta(days=2),  # diagnosed within the audit year
    )

    visit_date = audit_period.start_date + relativedelta(days=10)

    VisitFactory(
        patient=patient,
        visit_date=visit_date,
        flu_immunisation_recommended_date=visit_date,
    )

    submission = Submission.objects.create(
        paediatric_diabetes_unit=user.organisation_employers.first(),
        audit_year=audit_period.start_date.year,
        audit_period=audit_period,
        submission_date=audit_period.start_date,
        submission_by=user,
        submission_active=True,
    )
    submission.patients.add(patient)

    url = reverse(
        "pdu-patient-report",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )

    response = client.get(
        url + f"?category={TableCategories.ADDITIONAL_CARE_PROCESSES.value}",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == HTTPStatus.OK

    assert len(response.context["patients"]) == 1

    patient = response.context["patients"][0]

    assert patient["patient_identifier"] == "4444444444"
    assert patient["influenza_immunisation_recommended"] is True


@pytest.mark.parametrize("audit_period_slug", ["2024-2025", "2026-2027"])
@pytest.mark.django_db
def test_incomplete_year_patient_diagnosed_in_audit_year_excluded_from_totals(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    audit_period_slug,
):
    """
    Patients diagnosed within the audit year have is_complete_year_of_care=False.
    They should still appear as rows in the table, but must not be counted in the
    column header totals (total_eligible_*, total_passed_*).
    """
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()
    client = login_and_verify_user(client, user)

    audit_period = AuditPeriod.objects.get(slug=audit_period_slug)
    audit_period.is_open = True
    audit_period.save()

    dob = audit_period.start_date - relativedelta(years=14)

    # Complete-year patient: diagnosed before the audit period
    complete_patient = PatientFactory(
        nhs_number="5555555551",
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=dob,
        diagnosis_date=audit_period.start_date - relativedelta(years=2),
    )
    visit_date = audit_period.start_date + relativedelta(days=10)
    VisitFactory(
        patient=complete_patient,
        visit_date=visit_date,
        hba1c=50,
        hba1c_format=HBA1C_FORMATS[0][0],
        hba1c_date=visit_date,
    )

    # Incomplete-year patient: diagnosed inside the audit year
    incomplete_patient = PatientFactory(
        nhs_number="5555555552",
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=dob,
        diagnosis_date=audit_period.start_date + relativedelta(days=5),
    )
    visit_date2 = audit_period.start_date + relativedelta(days=15)
    VisitFactory(
        patient=incomplete_patient,
        visit_date=visit_date2,
        hba1c=60,
        hba1c_format=HBA1C_FORMATS[0][0],
        hba1c_date=visit_date2,
    )

    submission = Submission.objects.create(
        paediatric_diabetes_unit=user.organisation_employers.first(),
        audit_year=audit_period.start_date.year,
        audit_period=audit_period,
        submission_date=audit_period.start_date,
        submission_by=user,
        submission_active=True,
    )
    submission.patients.add(complete_patient, incomplete_patient)

    url = reverse(
        "pdu-patient-report",
        kwargs={"audit_period": audit_period.slug, "pz_code": ALDER_HEY_PZ_CODE},
    )
    response = client.get(
        url + f"?category={TableCategories.HEALTH_CHECKS.value}",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == HTTPStatus.OK

    # Both patients appear as rows
    assert len(response.context["patients"]) == 2

    # Totals count only the complete-year patient
    assert response.context["total_eligible_hba1c"] == 1, (
        "Incomplete-year patient (diagnosed in audit year) must not count in total_eligible"
    )
    assert response.context["total_passed_hba1c"] == 1, (
        "Incomplete-year patient (diagnosed in audit year) must not count in total_passed"
    )


@pytest.mark.parametrize("audit_period_slug", ["2024-2025", "2026-2027"])
@pytest.mark.django_db
def test_incomplete_year_patient_transferred_out_excluded_from_totals(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    audit_period_slug,
):
    """
    Patients who transferred out during the audit year have is_complete_year_of_care=False.
    They should still appear as rows in the table, but must not be counted in the
    column header totals (total_eligible_*, total_passed_*).
    """
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()
    client = login_and_verify_user(client, user)

    audit_period = AuditPeriod.objects.get(slug=audit_period_slug)
    audit_period.is_open = True
    audit_period.save()

    dob = audit_period.start_date - relativedelta(years=14)

    # Complete-year patient
    complete_patient = PatientFactory(
        nhs_number="5555555553",
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=dob,
        diagnosis_date=audit_period.start_date - relativedelta(years=2),
    )
    visit_date = audit_period.start_date + relativedelta(days=10)
    VisitFactory(
        patient=complete_patient,
        visit_date=visit_date,
        hba1c=50,
        hba1c_format=HBA1C_FORMATS[0][0],
        hba1c_date=visit_date,
    )

    # Incomplete-year patient: transferred out within the audit year
    transferred_patient = PatientFactory(
        nhs_number="5555555554",
        diabetes_type=DIABETES_TYPES[0][0],
        date_of_birth=dob,
        diagnosis_date=audit_period.start_date - relativedelta(years=2),
    )
    visit_date2 = audit_period.start_date + relativedelta(days=20)
    VisitFactory(
        patient=transferred_patient,
        visit_date=visit_date2,
        hba1c=60,
        hba1c_format=HBA1C_FORMATS[0][0],
        hba1c_date=visit_date2,
    )
    # Set the transfer date to within the audit year
    Transfer.objects.filter(patient=transferred_patient).update(
        date_leaving_service=audit_period.start_date + relativedelta(days=30)
    )

    submission = Submission.objects.create(
        paediatric_diabetes_unit=user.organisation_employers.first(),
        audit_year=audit_period.start_date.year,
        audit_period=audit_period,
        submission_date=audit_period.start_date,
        submission_by=user,
        submission_active=True,
    )
    submission.patients.add(complete_patient, transferred_patient)

    url = reverse(
        "pdu-patient-report",
        kwargs={"audit_period": audit_period.slug, "pz_code": ALDER_HEY_PZ_CODE},
    )
    response = client.get(
        url + f"?category={TableCategories.HEALTH_CHECKS.value}",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == HTTPStatus.OK

    # Both patients appear as rows
    assert len(response.context["patients"]) == 2

    # Totals count only the complete-year patient
    assert response.context["total_eligible_hba1c"] == 1, (
        "Transferred-out patient must not count in total_eligible"
    )
    assert response.context["total_passed_hba1c"] == 1, (
        "Transferred-out patient must not count in total_passed"
    )


@pytest.mark.parametrize(
    "audit_period_slug, smoking_field, non_smoker_val, smoker_val",
    [
        ("2024-2025", "smoking_status", SMOKING_STATUS[0][0], SMOKING_STATUS[1][0]),
        (
            "2026-2027",
            "smoking_vaping_status",
            SMOKING_VAPING_STATUS[0][0],
            SMOKING_VAPING_STATUS[1][0],
        ),
    ],
)
@pytest.mark.django_db
def test_patient_under_12yo_should_show_as_ineligible_for_smoking_status_screened(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    audit_period_slug,
    smoking_field,
    non_smoker_val,
    smoker_val,
):
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()

    client = login_and_verify_user(client, user)

    audit_period = AuditPeriod.objects.get(slug=audit_period_slug)
    audit_period.is_open = True
    audit_period.save()

    date_of_birth = audit_period.start_date - relativedelta(years=10)

    patient = PatientFactory(
        nhs_number="4444444444",
        diabetes_type=DIABETES_TYPES[0][0],  # T1DM
        date_of_birth=date_of_birth,
        diagnosis_date=audit_period.start_date - relativedelta(days=2),
    )

    visit_date = audit_period.start_date + relativedelta(days=10)

    VisitFactory(
        patient=patient,
        visit_date=visit_date,
        **{smoking_field: non_smoker_val},
    )

    submission = Submission.objects.create(
        paediatric_diabetes_unit=user.organisation_employers.first(),
        audit_year=audit_period.start_date.year,
        audit_period=audit_period,
        submission_date=audit_period.start_date,
        submission_by=user,
        submission_active=True,
    )
    submission.patients.add(patient)

    url = reverse(
        "pdu-patient-report",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )

    response = client.get(
        url + f"?category={TableCategories.ADDITIONAL_CARE_PROCESSES.value}",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == HTTPStatus.OK

    assert len(response.context["patients"]) == 1

    patient = response.context["patients"][0]

    assert patient["patient_identifier"] == "4444444444"
    assert patient["smoking_status"] is None


@pytest.mark.parametrize(
    "audit_period_slug, smoking_field, non_smoker_val, smoker_val",
    [
        ("2024-2025", "smoking_status", SMOKING_STATUS[0][0], SMOKING_STATUS[1][0]),
        (
            "2026-2027",
            "smoking_vaping_status",
            SMOKING_VAPING_STATUS[0][0],
            SMOKING_VAPING_STATUS[1][0],
        ),
    ],
)
@pytest.mark.django_db
def test_patient_over_12yo_non_smoker_should_not_be_eligible_for_smoking_cessation_referral(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    audit_period_slug,
    smoking_field,
    non_smoker_val,
    smoker_val,
):
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()

    client = login_and_verify_user(client, user)

    audit_period = AuditPeriod.objects.get(slug=audit_period_slug)
    audit_period.is_open = True
    audit_period.save()

    date_of_birth = audit_period.start_date - relativedelta(years=14)

    patient = PatientFactory(
        nhs_number="4444444444",
        diabetes_type=DIABETES_TYPES[0][0],  # T1DM
        date_of_birth=date_of_birth,
        diagnosis_date=audit_period.start_date - relativedelta(days=2),
    )

    visit_date = audit_period.start_date + relativedelta(days=10)

    VisitFactory(
        patient=patient,
        visit_date=visit_date,
        smoking_cessation_referral_date=None,
        **{smoking_field: non_smoker_val},
    )

    submission = Submission.objects.create(
        paediatric_diabetes_unit=user.organisation_employers.first(),
        audit_year=audit_period.start_date.year,
        audit_period=audit_period,
        submission_date=audit_period.start_date,
        submission_by=user,
        submission_active=True,
    )
    submission.patients.add(patient)

    url = reverse(
        "pdu-patient-report",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )

    response = client.get(
        url + f"?category={TableCategories.ADDITIONAL_CARE_PROCESSES.value}",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == HTTPStatus.OK

    assert len(response.context["patients"]) == 1

    patient = response.context["patients"][0]

    assert patient["patient_identifier"] == "4444444444"
    assert patient["smoking_status"] is True
    assert patient["smoking_cessation_referral"] == "non_smoker_no_referral"


# Retinal screening tests


@pytest.mark.parametrize("audit_period_slug", ["2024-2025", "2026-2027"])
@pytest.mark.django_db
def test_retinal_screening_under_12yo_shows_ineligible(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    audit_period_slug,
):
    """
    Test that patients under 12 years old show as ineligible for retinal screening.
    Result should be None regardless of whether data exists.
    """
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()

    client = login_and_verify_user(client, user)

    audit_period = AuditPeriod.objects.get(slug=audit_period_slug)
    audit_period.is_open = True
    audit_period.save()

    # Patient is 10 years old - under 12
    date_of_birth = audit_period.start_date - relativedelta(years=10)

    patient = PatientFactory(
        nhs_number="5555555555",
        diabetes_type=DIABETES_TYPES[0][0],  # T1DM
        date_of_birth=date_of_birth,
        diagnosis_date=audit_period.start_date - relativedelta(years=2),
    )

    visit_date = audit_period.start_date + relativedelta(days=10)

    # Create visit WITH retinal screening data
    VisitFactory(
        patient=patient,
        visit_date=visit_date,
        retinal_screening_result=1,  # Has screening result
        retinal_screening_observation_date=visit_date,
    )

    submission = Submission.objects.create(
        paediatric_diabetes_unit=user.organisation_employers.first(),
        audit_year=audit_period.start_date.year,
        audit_period=audit_period,
        submission_date=audit_period.start_date,
        submission_by=user,
        submission_active=True,
    )
    submission.patients.add(patient)

    url = reverse(
        "pdu-patient-report",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )

    response = client.get(
        url + f"?category={TableCategories.HEALTH_CHECKS.value}",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == HTTPStatus.OK

    patients = response.context["patients"]
    assert len(patients) == 1

    patient_data = patients[0]
    assert patient_data["patient_identifier"] == "5555555555"
    assert patient_data["is_gte_12yo"] is False
    # Should be "not_required" (ineligible) even though data exists
    assert patient_data["passed_retinal_screening"] == "not_required"


@pytest.mark.parametrize("audit_period_slug", ["2024-2025", "2026-2027"])
@pytest.mark.django_db
def test_retinal_screening_over_12yo_with_data_passes(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    audit_period_slug,
):
    """
    Test that patients 12+ years old with valid retinal screening data show as passed.
    Result should be True.
    """
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()

    client = login_and_verify_user(client, user)

    audit_period = AuditPeriod.objects.get(slug=audit_period_slug)
    audit_period.is_open = True
    audit_period.save()

    # Patient is 14 years old - over 12
    date_of_birth = audit_period.start_date - relativedelta(years=14)

    patient = PatientFactory(
        nhs_number="6666666666",
        diabetes_type=DIABETES_TYPES[0][0],  # T1DM
        date_of_birth=date_of_birth,
        diagnosis_date=audit_period.start_date - relativedelta(years=2),
    )

    visit_date = audit_period.start_date + relativedelta(days=10)

    # Create visit WITH retinal screening data
    VisitFactory(
        patient=patient,
        visit_date=visit_date,
        retinal_screening_result=1,  # Valid screening result
        retinal_screening_observation_date=visit_date,
    )

    submission = Submission.objects.create(
        paediatric_diabetes_unit=user.organisation_employers.first(),
        audit_year=audit_period.start_date.year,
        audit_period=audit_period,
        submission_date=audit_period.start_date,
        submission_by=user,
        submission_active=True,
    )
    submission.patients.add(patient)

    url = reverse(
        "pdu-patient-report",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )

    response = client.get(
        url + f"?category={TableCategories.HEALTH_CHECKS.value}",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == HTTPStatus.OK

    patients = response.context["patients"]
    assert len(patients) == 1

    patient_data = patients[0]
    assert patient_data["patient_identifier"] == "6666666666"
    assert patient_data["is_gte_12yo"] is True
    # Should pass because they are 12+ with valid data
    assert patient_data["passed_retinal_screening"] == "complete"


@pytest.mark.parametrize("audit_period_slug", ["2024-2025", "2026-2027"])
@pytest.mark.django_db
def test_retinal_screening_over_12yo_with_data_fails(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    audit_period_slug,
):
    """
    Test that patients 12+ years old who are eligible but don't pass show as failed.
    Result should be False.
    """
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()

    client = login_and_verify_user(client, user)

    audit_period = AuditPeriod.objects.get(slug=audit_period_slug)
    audit_period.is_open = True
    audit_period.save()

    # Patient is 13 years old - over 12
    date_of_birth = audit_period.start_date - relativedelta(years=13)

    patient = PatientFactory(
        nhs_number="7777777777",
        diabetes_type=DIABETES_TYPES[0][0],  # T1DM
        date_of_birth=date_of_birth,
        diagnosis_date=audit_period.start_date - relativedelta(years=2),
    )

    visit_date = audit_period.start_date + relativedelta(days=10)

    # Create visit WITHOUT valid retinal screening (or with invalid result)
    VisitFactory(
        patient=patient,
        visit_date=visit_date,
        retinal_screening_result=None,  # No valid screening
        retinal_screening_observation_date=visit_date,  # But has a date (eligible)
    )

    submission = Submission.objects.create(
        paediatric_diabetes_unit=user.organisation_employers.first(),
        audit_year=audit_period.start_date.year,
        audit_period=audit_period,
        submission_date=audit_period.start_date,
        submission_by=user,
        submission_active=True,
    )
    submission.patients.add(patient)

    url = reverse(
        "pdu-patient-report",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )

    response = client.get(
        url + f"?category={TableCategories.HEALTH_CHECKS.value}",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == HTTPStatus.OK

    patients = response.context["patients"]
    assert len(patients) == 1

    patient_data = patients[0]
    assert patient_data["patient_identifier"] == "7777777777"
    assert patient_data["is_gte_12yo"] is True
    # Should be blank because they are eligible but don't pass — eye screen is biannual
    assert patient_data["passed_retinal_screening"] == ""


@pytest.mark.parametrize("audit_period_slug", ["2024-2025", "2026-2027"])
@pytest.mark.django_db
def test_retinal_screening_over_12yo_without_data_shows_blank(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    audit_period_slug,
):
    """
    Test that patients 12+ years old with NO retinal screening data show as blank.
    Result should be None (but different meaning than under 12).
    """
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()

    client = login_and_verify_user(client, user)

    audit_period = AuditPeriod.objects.get(slug=audit_period_slug)
    audit_period.is_open = True
    audit_period.save()

    # Patient is 15 years old - over 12
    date_of_birth = audit_period.start_date - relativedelta(years=15)

    patient = PatientFactory(
        nhs_number="8888888888",
        diabetes_type=DIABETES_TYPES[0][0],  # T1DM
        date_of_birth=date_of_birth,
        diagnosis_date=audit_period.start_date - relativedelta(years=2),
    )

    visit_date = audit_period.start_date + relativedelta(days=10)

    # Create visit WITHOUT any retinal screening data
    VisitFactory(
        patient=patient,
        visit_date=visit_date,
        retinal_screening_result=None,
        retinal_screening_observation_date=None,  # No data at all
    )

    submission = Submission.objects.create(
        paediatric_diabetes_unit=user.organisation_employers.first(),
        audit_year=audit_period.start_date.year,
        audit_period=audit_period,
        submission_date=audit_period.start_date,
        submission_by=user,
        submission_active=True,
    )
    submission.patients.add(patient)

    url = reverse(
        "pdu-patient-report",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )

    response = client.get(
        url + f"?category={TableCategories.HEALTH_CHECKS.value}",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == HTTPStatus.OK

    patients = response.context["patients"]
    assert len(patients) == 1

    patient_data = patients[0]
    assert patient_data["patient_identifier"] == "8888888888"
    assert patient_data["is_gte_12yo"] is True
    # Should be blank (no data available) - template will show blank, not ineligible icon
    assert patient_data["passed_retinal_screening"] == ""


@pytest.mark.parametrize(
    "audit_period_slug, smoking_field, non_smoker_val, smoker_val",
    [
        ("2024-2025", "smoking_status", SMOKING_STATUS[0][0], SMOKING_STATUS[1][0]),
        (
            "2026-2027",
            "smoking_vaping_status",
            SMOKING_VAPING_STATUS[0][0],
            SMOKING_VAPING_STATUS[1][0],
        ),
    ],
)
@pytest.mark.django_db
def test_patient_with_two_visits_one_with_smoking_status_one_without_has_one_row_in_the_patient_report(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    audit_period_slug,
    smoking_field,
    non_smoker_val,
    smoker_val,
):
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()

    client = login_and_verify_user(client, user)

    audit_period = AuditPeriod.objects.get(slug=audit_period_slug)
    audit_period.is_open = True
    audit_period.save()

    date_of_birth = audit_period.start_date - relativedelta(years=14)

    patient = PatientFactory(
        nhs_number="4444444444",
        diabetes_type=DIABETES_TYPES[0][0],  # T1DM
        date_of_birth=date_of_birth,
        diagnosis_date=audit_period.start_date - relativedelta(days=2),
    )

    visit_date_1 = audit_period.start_date + relativedelta(days=10)
    visit_date_2 = audit_period.start_date + relativedelta(days=20)

    # First visit WITHOUT smoking status
    VisitFactory(
        patient=patient,
        visit_date=visit_date_1,
        **{smoking_field: None},
    )

    # Second visit WITH smoking status
    VisitFactory(
        patient=patient,
        visit_date=visit_date_2,
        **{smoking_field: non_smoker_val},
    )

    submission = Submission.objects.create(
        paediatric_diabetes_unit=user.organisation_employers.first(),
        audit_year=audit_period.start_date.year,
        audit_period=audit_period,
        submission_date=audit_period.start_date,
        submission_by=user,
        submission_active=True,
    )
    submission.patients.add(patient)

    url = reverse(
        "pdu-patient-report",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )

    response = client.get(
        url + f"?category={TableCategories.ADDITIONAL_CARE_PROCESSES.value}",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == HTTPStatus.OK

    assert len(response.context["patients"]) == 1

    patient = response.context["patients"][0]

    assert patient["patient_identifier"] == "4444444444"
    assert patient["smoking_status"] is True  # from the second visit


@pytest.mark.parametrize(
    "audit_period_slug, smoking_field, non_smoker_val, smoker_val",
    [
        ("2024-2025", "smoking_status", SMOKING_STATUS[0][0], SMOKING_STATUS[1][0]),
        (
            "2026-2027",
            "smoking_vaping_status",
            SMOKING_VAPING_STATUS[0][0],
            SMOKING_VAPING_STATUS[1][0],
        ),
    ],
)
@pytest.mark.django_db
def test_smoker_with_two_visits_one_with_smoking_cessation_referral_one_without_has_one_row_in_the_patient_report(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    audit_period_slug,
    smoking_field,
    non_smoker_val,
    smoker_val,
):
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()

    client = login_and_verify_user(client, user)

    audit_period = AuditPeriod.objects.get(slug=audit_period_slug)
    audit_period.is_open = True
    audit_period.save()

    date_of_birth = audit_period.start_date - relativedelta(years=14)

    patient = PatientFactory(
        nhs_number="4444444444",
        diabetes_type=DIABETES_TYPES[0][0],  # T1DM
        date_of_birth=date_of_birth,
        diagnosis_date=audit_period.start_date - relativedelta(days=2),
    )

    visit_date_1 = audit_period.start_date + relativedelta(days=10)
    visit_date_2 = audit_period.start_date + relativedelta(days=20)

    # First visit WITH smoking status and cessation referral
    VisitFactory(
        patient=patient,
        visit_date=visit_date_1,
        smoking_cessation_referral_date=visit_date_1,
        **{smoking_field: smoker_val},
    )

    # Second visit WITHOUT smoking data
    VisitFactory(patient=patient, visit_date=visit_date_2)

    submission = Submission.objects.create(
        paediatric_diabetes_unit=user.organisation_employers.first(),
        audit_year=audit_period.start_date.year,
        audit_period=audit_period,
        submission_date=audit_period.start_date,
        submission_by=user,
        submission_active=True,
    )
    submission.patients.add(patient)

    url = reverse(
        "pdu-patient-report",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )

    response = client.get(
        url + f"?category={TableCategories.ADDITIONAL_CARE_PROCESSES.value}",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == HTTPStatus.OK

    assert len(response.context["patients"]) == 1

    patient = response.context["patients"][0]

    assert patient["patient_identifier"] == "4444444444"
    assert patient["smoking_status"] is True  # from the first visit
    assert patient["smoking_cessation_referral"] == "True"  # from the first visit


@pytest.mark.parametrize(
    "audit_period_slug, smoking_field, non_smoker_val, smoker_val",
    [
        ("2024-2025", "smoking_status", SMOKING_STATUS[0][0], SMOKING_STATUS[1][0]),
        (
            "2026-2027",
            "smoking_vaping_status",
            SMOKING_VAPING_STATUS[0][0],
            SMOKING_VAPING_STATUS[1][0],
        ),
    ],
)
@pytest.mark.django_db
def test_smoking_cessation_referral_column_denominator_is_smokers_only(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    audit_period_slug,
    smoking_field,
    non_smoker_val,
    smoker_val,
):
    """
    The 'Referral to smoking cessation service' column header facet should
    show X / <smokers ≥ 12>, NOT X / <all T1 patients ≥ 12>.

    Non-smokers are 'not required' for this measure, so they must not be
    counted in the denominator.

    Setup:
        patient_smoker_referred   – ≥12, T1DM, smoker, cessation referral  → passes
        patient_smoker_no_ref     – ≥12, T1DM, smoker, no cessation referral → fails
        patient_non_smoker        – ≥12, T1DM, non-smoker                  → not required
        patient_under_12          – <12, T1DM                               → not required (age)

    Expected column header:  1 / 2  (only the two smokers are the denominator)
    """
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()
    client = login_and_verify_user(client, user)

    audit_period = AuditPeriod.objects.get(slug=audit_period_slug)
    audit_period.is_open = True
    audit_period.save()

    Patient.objects.all().delete()

    start = audit_period.start_date

    base_criteria = {
        "diabetes_type": DIABETES_TYPES[0][0],  # T1DM
        "diagnosis_date": start - relativedelta(years=2),
        "transfer__date_leaving_service": None,
    }

    # ≥12 yo, smoker, has cessation referral → should PASS
    patient_smoker_referred = PatientFactory(
        nhs_number="1111111111",
        date_of_birth=start - relativedelta(years=14),
        **base_criteria,
    )
    VisitFactory(
        patient=patient_smoker_referred,
        visit_date=start + relativedelta(days=10),
        height_weight_observation_date=start + relativedelta(days=10),
        smoking_cessation_referral_date=start + relativedelta(days=10),
        **{smoking_field: smoker_val},
    )

    # ≥12 yo, smoker, no cessation referral → should FAIL (still in denominator)
    patient_smoker_no_ref = PatientFactory(
        nhs_number="2222222222",
        date_of_birth=start - relativedelta(years=14),
        **base_criteria,
    )
    VisitFactory(
        patient=patient_smoker_no_ref,
        visit_date=start + relativedelta(days=10),
        height_weight_observation_date=start + relativedelta(days=10),
        smoking_cessation_referral_date=None,
        **{smoking_field: smoker_val},
    )

    # ≥12 yo, non-smoker → NOT required, must NOT be counted in denominator
    patient_non_smoker = PatientFactory(
        nhs_number="3333333333",
        date_of_birth=start - relativedelta(years=14),
        **base_criteria,
    )
    VisitFactory(
        patient=patient_non_smoker,
        visit_date=start + relativedelta(days=10),
        smoking_cessation_referral_date=None,
        **{smoking_field: non_smoker_val},
    )

    # <12 yo → NOT required (age), must NOT be counted in denominator
    patient_under_12 = PatientFactory(
        nhs_number="4444444444",
        date_of_birth=start - relativedelta(years=10),
        **base_criteria,
    )
    VisitFactory(
        patient=patient_under_12,
        visit_date=start + relativedelta(days=10),
    )

    submission = Submission.objects.create(
        paediatric_diabetes_unit=user.organisation_employers.first(),
        audit_year=audit_period.start_date.year,
        audit_period=audit_period,
        submission_date=start,
        submission_by=user,
        submission_active=True,
    )
    submission.patients.add(
        patient_smoker_referred,
        patient_smoker_no_ref,
        patient_non_smoker,
        patient_under_12,
    )

    url = reverse(
        "pdu-patient-report",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )
    response = client.get(
        url + f"?category={TableCategories.ADDITIONAL_CARE_PROCESSES.value}",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == HTTPStatus.OK

    # Only the two smokers should be in the denominator
    assert response.context["total_eligible_smoking_cessation_referral"] == 2, (
        "Denominator should be smokers ≥12 only, not all T1 patients ≥12"
    )
    # Only the one with a referral should pass
    assert response.context["total_passed_smoking_cessation_referral"] == 1


@pytest.mark.django_db
def test_treatment_missing_penultimate_visit_counted(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture, client
):
    """
    When the most recent visit has no treatment value, the treatment_regimen
    annotation should fall back to the most recent visit that does have a value.
    """
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()

    client = login_and_verify_user(client, user)

    audit_period = AuditPeriod.objects.get_default_audit_period()
    audit_period.is_open = True
    audit_period.save()

    date_of_birth = audit_period.start_date - relativedelta(years=10)

    patient = PatientFactory(
        nhs_number="5555555555",
        diabetes_type=DIABETES_TYPES[0][0],  # T1DM
        date_of_birth=date_of_birth,
        diagnosis_date=audit_period.start_date - relativedelta(years=2),
    )

    visit_date = audit_period.start_date + relativedelta(days=10)

    # Earlier visit WITH treatment data
    VisitFactory(
        patient=patient,
        visit_date=visit_date,
        treatment=TREATMENT_TYPES[2][0],  # 3 = "Insulin pump"
    )

    # Most recent visit WITHOUT treatment data — the earlier value should still be used
    VisitFactory(
        patient=patient,
        visit_date=visit_date + relativedelta(days=30),
        treatment=None,
    )

    submission = Submission.objects.create(
        paediatric_diabetes_unit=user.organisation_employers.first(),
        audit_year=audit_period.start_date.year,
        audit_period=audit_period,
        submission_date=audit_period.start_date,
        submission_by=user,
        submission_active=True,
    )
    submission.patients.add(patient)

    url = reverse(
        "pdu-patient-report",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )

    response = client.get(
        url + f"?category={TableCategories.TREATMENT.value}",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == HTTPStatus.OK

    patients = response.context["patients"]
    assert len(patients) == 1

    patient_data = patients[0]
    assert patient_data["patient_identifier"] == "5555555555"
    # Should use the earlier visit's treatment, not "No treatment regimen"
    assert patient_data["treatment_regimen"] == TREATMENT_TYPES[2][1]  # "Insulin pump"


@pytest.mark.django_db
def test_glucose_monitoring_missing_penultimate_visit_counted(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture, client
):
    """
    When the most recent visit has no glucose_monitoring value, the annotation
    should fall back to the most recent visit that does have a value.
    """
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()

    client = login_and_verify_user(client, user)

    audit_period = AuditPeriod.objects.get_default_audit_period()
    audit_period.is_open = True
    audit_period.save()

    date_of_birth = audit_period.start_date - relativedelta(years=10)

    patient = PatientFactory(
        nhs_number="5555555556",
        diabetes_type=DIABETES_TYPES[0][0],  # T1DM
        date_of_birth=date_of_birth,
        diagnosis_date=audit_period.start_date - relativedelta(years=2),
    )

    visit_date = audit_period.start_date + relativedelta(days=10)

    # Earlier visit WITH glucose monitoring data
    VisitFactory(
        patient=patient,
        visit_date=visit_date,
        glucose_monitoring=GLUCOSE_MONITORING_TYPES[1][
            0
        ],  # 2 = "Flash glucose monitor"
    )

    # Most recent visit WITHOUT glucose monitoring data — the earlier value should still be used
    VisitFactory(
        patient=patient,
        visit_date=visit_date + relativedelta(days=30),
        glucose_monitoring=None,
    )

    submission = Submission.objects.create(
        paediatric_diabetes_unit=user.organisation_employers.first(),
        audit_year=audit_period.start_date.year,
        audit_period=audit_period,
        submission_date=audit_period.start_date,
        submission_by=user,
        submission_active=True,
    )
    submission.patients.add(patient)

    url = reverse(
        "pdu-patient-report",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )

    response = client.get(
        url + f"?category={TableCategories.TREATMENT.value}",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == HTTPStatus.OK

    patients = response.context["patients"]
    assert len(patients) == 1

    patient_data = patients[0]
    assert patient_data["patient_identifier"] == "5555555556"
    # Should use the earlier visit's glucose monitoring, not "No glucose monitoring"
    assert (
        patient_data["glucose_monitoring"] == GLUCOSE_MONITORING_TYPES[1][1]
    )  # "Flash glucose monitor"


@pytest.mark.django_db
def test_hcl_missing_penultimate_visit_counted(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture, client
):
    """
    When the most recent visit has no closed_loop_system value, the hcl
    annotation should fall back to the most recent visit that does have a value.
    """
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()

    client = login_and_verify_user(client, user)

    audit_period = AuditPeriod.objects.get_default_audit_period()
    audit_period.is_open = True
    audit_period.save()

    date_of_birth = audit_period.start_date - relativedelta(years=10)

    patient = PatientFactory(
        nhs_number="5555555557",
        diabetes_type=DIABETES_TYPES[0][0],  # T1DM
        date_of_birth=date_of_birth,
        diagnosis_date=audit_period.start_date - relativedelta(years=2),
    )

    visit_date = audit_period.start_date + relativedelta(days=10)

    # Earlier visit WITH HCL data (value 2 = licenced closed loop → hcl = "Yes")
    VisitFactory(
        patient=patient,
        visit_date=visit_date,
        closed_loop_system=CLOSED_LOOP_TYPES[1][
            0
        ],  # 2 = "Closed loop system (licenced)"
    )

    # Most recent visit WITHOUT HCL data — the earlier value should still be used
    VisitFactory(
        patient=patient,
        visit_date=visit_date + relativedelta(days=30),
        closed_loop_system=None,
    )

    submission = Submission.objects.create(
        paediatric_diabetes_unit=user.organisation_employers.first(),
        audit_year=audit_period.start_date.year,
        audit_period=audit_period,
        submission_date=audit_period.start_date,
        submission_by=user,
        submission_active=True,
    )
    submission.patients.add(patient)

    url = reverse(
        "pdu-patient-report",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )

    response = client.get(
        url + f"?category={TableCategories.TREATMENT.value}",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == HTTPStatus.OK

    patients = response.context["patients"]
    assert len(patients) == 1

    patient_data = patients[0]
    assert patient_data["patient_identifier"] == "5555555557"
    # Should use the earlier visit's closed loop value, not the default "No"
    assert patient_data["hcl"] == "Yes"


# ── 2026 dataset treatment fallback tests ─────────────────────────────────────
# These three tests cover the same "fall back to most recent non-null visit"
# behaviour as the 2021 tests above, but for the 2026 dataset fields:
#   treatment        → insulin_regimen
#   glucose_monitoring → cgm_use  (YES_NO_UNKNOWN)
#   closed_loop_system → insulin_regimen == 5  (HCL embedded in insulin regimen)
#
# They are expected to FAIL until annotate_treatment branches on dataset_year.


@pytest.mark.django_db
def test_insulin_regimen_2026_missing_penultimate_visit_counted(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture, client
):
    """
    2026 dataset: when the most recent visit has no insulin_regimen value, the
    treatment_regimen annotation should fall back to the most recent visit that
    does have a value.
    """
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()

    client = login_and_verify_user(client, user)

    audit_period = AuditPeriod.objects.get(slug="2026-2027")
    audit_period.is_open = True
    audit_period.save()

    date_of_birth = audit_period.start_date - relativedelta(years=10)

    patient = PatientFactory(
        nhs_number="6666666661",
        diabetes_type=DIABETES_TYPES[0][0],  # T1DM
        date_of_birth=date_of_birth,
        diagnosis_date=audit_period.start_date - relativedelta(years=2),
    )

    visit_date = audit_period.start_date + relativedelta(days=10)

    # Earlier visit WITH insulin_regimen data (4 = "Insulin pump (standalone)")
    VisitFactory(
        patient=patient,
        visit_date=visit_date,
        insulin_regimen=INSULIN_TREATMENT[3][0],  # 4 = "Insulin pump (standalone)"
        treatment=None,
    )

    # Most recent visit WITHOUT insulin_regimen — earlier value should still be used
    VisitFactory(
        patient=patient,
        visit_date=visit_date + relativedelta(days=30),
        insulin_regimen=None,
        treatment=None,
    )

    submission = Submission.objects.create(
        paediatric_diabetes_unit=user.organisation_employers.first(),
        audit_year=audit_period.start_date.year,
        audit_period=audit_period,
        submission_date=audit_period.start_date,
        submission_by=user,
        submission_active=True,
    )
    submission.patients.add(patient)

    url = reverse(
        "pdu-patient-report",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )

    response = client.get(
        url + f"?category={TableCategories.TREATMENT.value}",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == HTTPStatus.OK

    patients = response.context["patients"]
    assert len(patients) == 1

    patient_data = patients[0]
    assert patient_data["patient_identifier"] == "6666666661"
    # Should use the earlier visit's insulin_regimen, not "No treatment regimen"
    assert (
        patient_data["treatment_regimen"] == INSULIN_TREATMENT[3][1]
    )  # "Insulin pump (standalone)"


@pytest.mark.django_db
def test_cgm_use_2026_missing_penultimate_visit_counted(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture, client
):
    """
    2026 dataset: when the most recent visit has no cgm_use value, the
    glucose_monitoring annotation should fall back to the most recent visit that
    does have a value.
    """
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()

    client = login_and_verify_user(client, user)

    audit_period = AuditPeriod.objects.get(slug="2026-2027")
    audit_period.is_open = True
    audit_period.save()

    date_of_birth = audit_period.start_date - relativedelta(years=10)

    patient = PatientFactory(
        nhs_number="6666666662",
        diabetes_type=DIABETES_TYPES[0][0],  # T1DM
        date_of_birth=date_of_birth,
        diagnosis_date=audit_period.start_date - relativedelta(years=2),
    )

    visit_date = audit_period.start_date + relativedelta(days=10)

    # Earlier visit WITH cgm_use data (1 = "Yes")
    VisitFactory(
        patient=patient,
        visit_date=visit_date,
        cgm_use=YES_NO_UNKNOWN[0][0],  # 1 = "Yes"
        glucose_monitoring=None,
    )

    # Most recent visit WITHOUT cgm_use — earlier value should still be used
    VisitFactory(
        patient=patient,
        visit_date=visit_date + relativedelta(days=30),
        cgm_use=None,
        glucose_monitoring=None,
    )

    submission = Submission.objects.create(
        paediatric_diabetes_unit=user.organisation_employers.first(),
        audit_year=audit_period.start_date.year,
        audit_period=audit_period,
        submission_date=audit_period.start_date,
        submission_by=user,
        submission_active=True,
    )
    submission.patients.add(patient)

    url = reverse(
        "pdu-patient-report",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )

    response = client.get(
        url + f"?category={TableCategories.TREATMENT.value}",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == HTTPStatus.OK

    patients = response.context["patients"]
    assert len(patients) == 1

    patient_data = patients[0]
    assert patient_data["patient_identifier"] == "6666666662"
    # Should use the earlier visit's cgm_use, not "No glucose monitoring"
    assert patient_data["glucose_monitoring"] == YES_NO_UNKNOWN[0][1]  # "Yes"


@pytest.mark.django_db
def test_hcl_from_insulin_regimen_2026_missing_penultimate_visit_counted(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture, client
):
    """
    2026 dataset: HCL is encoded as insulin_regimen == 5 ("Hybrid closed loop").
    When the most recent visit has no insulin_regimen, the hcl annotation should
    fall back to the most recent visit that does have a value, and derive
    hcl="Yes" from insulin_regimen==5.
    """
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=test_user_audit_centre_editor_data.role,
    ).first()

    client = login_and_verify_user(client, user)

    audit_period = AuditPeriod.objects.get(slug="2026-2027")
    audit_period.is_open = True
    audit_period.save()

    date_of_birth = audit_period.start_date - relativedelta(years=10)

    patient = PatientFactory(
        nhs_number="6666666663",
        diabetes_type=DIABETES_TYPES[0][0],  # T1DM
        date_of_birth=date_of_birth,
        diagnosis_date=audit_period.start_date - relativedelta(years=2),
    )

    visit_date = audit_period.start_date + relativedelta(days=10)

    # Earlier visit WITH insulin_regimen == 5 (Hybrid closed loop → hcl = "Yes")
    VisitFactory(
        patient=patient,
        visit_date=visit_date,
        insulin_regimen=INSULIN_TREATMENT[4][0],  # 5 = "Hybrid closed loop"
        treatment=None,
    )

    # Most recent visit WITHOUT insulin_regimen — earlier value should still be used
    VisitFactory(
        patient=patient,
        visit_date=visit_date + relativedelta(days=30),
        insulin_regimen=None,
        treatment=None,
    )

    submission = Submission.objects.create(
        paediatric_diabetes_unit=user.organisation_employers.first(),
        audit_year=audit_period.start_date.year,
        audit_period=audit_period,
        submission_date=audit_period.start_date,
        submission_by=user,
        submission_active=True,
    )
    submission.patients.add(patient)

    url = reverse(
        "pdu-patient-report",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )

    response = client.get(
        url + f"?category={TableCategories.TREATMENT.value}",
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == HTTPStatus.OK

    patients = response.context["patients"]
    assert len(patients) == 1

    patient_data = patients[0]
    assert patient_data["patient_identifier"] == "6666666663"
    # insulin_regimen == 5 means HCL, should derive hcl = "Yes"
    assert patient_data["hcl"] == "Yes"
