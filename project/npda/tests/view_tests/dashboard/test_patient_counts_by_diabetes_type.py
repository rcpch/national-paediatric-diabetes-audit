"""Tests for the patient_ages dashboard view."""

from http import HTTPStatus

import pytest
from dateutil.relativedelta import relativedelta
from django.urls import reverse

from project.constants.diabetes_types import DIABETES_TYPES
from project.npda.models import AuditPeriod, NPDAUser, Submission
from project.npda.tests.constants_for_tests import ALDER_HEY_PZ_CODE
from project.npda.tests.factories import test_user_audit_centre_editor_data
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.utils import login_and_verify_user

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_user():
    return NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
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
        "pdu-patient-ages",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
        },
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_patient_ages_no_submission(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    """When there is no active submission all age band and sex counts are zero."""
    user = _get_user()
    audit_period = AuditPeriod.objects.get_default_audit_period()

    client = login_and_verify_user(client, user)
    response = client.get(_url(audit_period))

    assert response.status_code == HTTPStatus.OK
    assert response.context["number_of_patients"] == 0
    assert all(v == 0 for v in response.context["patients_by_age"].values())
    assert all(v == 0 for v in response.context["patients_by_sex"].values())


@pytest.mark.parametrize(
    "age_at_start, expected_band",
    [
        pytest.param(1, "birth_two", id="age_1_in_birth_two"),
        pytest.param(3, "two_five", id="age_3_in_two_five"),
        pytest.param(8, "five_twelve", id="age_8_in_five_twelve"),
        pytest.param(14, "twelve_sixteen", id="age_14_in_twelve_sixteen"),
        pytest.param(17, "sixteen_nineteen", id="age_17_in_sixteen_nineteen"),
        pytest.param(21, "nineteen_twenty_five", id="age_21_in_nineteen_twenty_five"),
    ],
)
@pytest.mark.django_db
def test_patient_ages_age_band_assignment(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
    age_at_start,
    expected_band,
):
    """A patient exactly `age_at_start` years old on audit start lands in the correct band."""
    user = _get_user()
    audit_period = AuditPeriod.objects.get_default_audit_period()

    patient = PatientFactory(
        date_of_birth=audit_period.start_date - relativedelta(years=age_at_start),
        sex=1,  # Male
        diabetes_type=DIABETES_TYPES[0][0],  # T1DM
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )

    submission = _create_submission(user, audit_period)
    submission.patients.add(patient)

    client = login_and_verify_user(client, user)
    response = client.get(_url(audit_period))

    assert response.status_code == HTTPStatus.OK
    patients_by_age = response.context["patients_by_age"]
    assert patients_by_age[expected_band] == 1
    # All other detailed bands (excluding the aggregate tallies) must be zero
    detail_bands = {
        "birth_two",
        "two_five",
        "five_twelve",
        "twelve_sixteen",
        "sixteen_nineteen",
        "nineteen_twenty_five",
    }
    for band in detail_bands - {expected_band}:
        assert (
            patients_by_age[band] == 0
        ), f"Expected {band} to be 0, got {patients_by_age[band]}"


@pytest.mark.django_db
def test_patient_ages_calculated_from_audit_start_not_today(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    """
    Ages must be calculated from audit_period.start_date, not from today's date.

    A patient born exactly 11 years before audit start (2013-04-01 for the 2024
    audit period) is 11 on audit start → five_twelve.  By today (2026-03-25) they
    are 12, so using today's date would incorrectly place them in twelve_sixteen.
    """
    user = _get_user()
    audit_period = (
        AuditPeriod.objects.get_default_audit_period()
    )  # start_date = 2024-04-01

    # Patient is exactly 11 on audit start date, but 12 when evaluated from today
    patient = PatientFactory(
        date_of_birth=audit_period.start_date - relativedelta(years=11),
        sex=1,
        diabetes_type=DIABETES_TYPES[0][0],
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )

    submission = _create_submission(user, audit_period)
    submission.patients.add(patient)

    client = login_and_verify_user(client, user)
    response = client.get(_url(audit_period))

    assert response.status_code == HTTPStatus.OK
    patients_by_age = response.context["patients_by_age"]
    # Correct: age from audit start → 11 → five_twelve
    assert patients_by_age["five_twelve"] == 1
    assert patients_by_age["under_twelve"] == 1
    # Would be wrong if today's date were used (patient would be 12 → twelve_sixteen)
    assert patients_by_age["twelve_sixteen"] == 0
    assert patients_by_age["over_twelve"] == 0


@pytest.mark.django_db
def test_patient_ages_under_and_over_twelve(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    """under_twelve and over_twelve aggregate tallies are correct."""
    user = _get_user()
    audit_period = AuditPeriod.objects.get_default_audit_period()

    young_patient = PatientFactory(
        date_of_birth=audit_period.start_date - relativedelta(years=8),
        sex=1,
        diabetes_type=DIABETES_TYPES[0][0],
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )
    older_patient = PatientFactory(
        date_of_birth=audit_period.start_date - relativedelta(years=14),
        sex=2,
        diabetes_type=DIABETES_TYPES[0][0],
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )

    submission = _create_submission(user, audit_period)
    submission.patients.add(young_patient, older_patient)

    client = login_and_verify_user(client, user)
    response = client.get(_url(audit_period))

    assert response.status_code == HTTPStatus.OK
    patients_by_age = response.context["patients_by_age"]
    assert patients_by_age["under_twelve"] == 1
    assert patients_by_age["over_twelve"] == 1
    assert patients_by_age["five_twelve"] == 1
    assert patients_by_age["twelve_sixteen"] == 1


@pytest.mark.django_db
def test_patient_ages_sex_counts(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    """Male and female patients are each counted in the correct sex bucket."""
    user = _get_user()
    audit_period = AuditPeriod.objects.get_default_audit_period()

    male_patient = PatientFactory(
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        sex=1,  # Male
        diabetes_type=DIABETES_TYPES[0][0],
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )
    female_patient = PatientFactory(
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        sex=2,  # Female
        diabetes_type=DIABETES_TYPES[0][0],
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )

    submission = _create_submission(user, audit_period)
    submission.patients.add(male_patient, female_patient)

    client = login_and_verify_user(client, user)
    response = client.get(_url(audit_period))

    assert response.status_code == HTTPStatus.OK
    assert response.context["number_of_patients"] == 2
    patients_by_sex = response.context["patients_by_sex"]
    assert patients_by_sex["male"] == 1
    assert patients_by_sex["female"] == 1
    assert patients_by_sex["not_known"] == 0
    assert patients_by_sex["not_specified"] == 0


@pytest.mark.django_db
def test_patient_ages_filter_by_diabetes_type(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    """POSTing a diabetes_type value filters patient counts to only that type."""
    user = _get_user()
    audit_period = AuditPeriod.objects.get_default_audit_period()

    t1_patient = PatientFactory(
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        sex=1,
        diabetes_type=DIABETES_TYPES[0][0],  # T1DM = 1
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )
    t2_patient = PatientFactory(
        date_of_birth=audit_period.start_date - relativedelta(years=15),
        sex=2,
        diabetes_type=DIABETES_TYPES[1][0],  # T2DM = 2
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )

    submission = _create_submission(user, audit_period)
    submission.patients.add(t1_patient, t2_patient)

    client = login_and_verify_user(client, user)

    # Filter to T1DM only
    response = client.post(
        _url(audit_period),
        data={"diabetes_type": str(DIABETES_TYPES[0][0])},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.context["number_of_patients"] == 1
    patients_by_age = response.context["patients_by_age"]
    # T1 patient is 10 years old → five_twelve band
    assert patients_by_age["five_twelve"] == 1
    # T2 patient (15 years → twelve_sixteen) must be excluded
    assert patients_by_age["twelve_sixteen"] == 0


@pytest.mark.django_db
def test_patient_ages_all_diabetes_types_selected(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    """POSTing diabetes_type=0 ('All') returns counts across all diabetes types."""
    user = _get_user()
    audit_period = AuditPeriod.objects.get_default_audit_period()

    t1_patient = PatientFactory(
        date_of_birth=audit_period.start_date - relativedelta(years=10),
        sex=1,
        diabetes_type=DIABETES_TYPES[0][0],  # T1DM
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )
    t2_patient = PatientFactory(
        date_of_birth=audit_period.start_date - relativedelta(years=15),
        sex=2,
        diabetes_type=DIABETES_TYPES[1][0],  # T2DM
        diagnosis_date=audit_period.start_date - relativedelta(days=1),
    )

    submission = _create_submission(user, audit_period)
    submission.patients.add(t1_patient, t2_patient)

    client = login_and_verify_user(client, user)

    # diabetes_type=0 means "All" → no type filter applied
    response = client.post(
        _url(audit_period),
        data={"diabetes_type": "0"},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.context["number_of_patients"] == 2
    patients_by_age = response.context["patients_by_age"]
    assert patients_by_age["five_twelve"] == 1  # T1 patient aged 10
    assert patients_by_age["twelve_sixteen"] == 1  # T2 patient aged 15
