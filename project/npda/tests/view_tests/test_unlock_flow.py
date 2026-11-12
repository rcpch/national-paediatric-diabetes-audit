"""
Tests for the audit team "unlock" flow on patients in transfer.

Patients in transfer have their visits locked in the UI. Audit team members
should see the "Unlock (Audit Team only)" button for them (as they do for CSV
uploads and inactive PDUs), and unlocking should re-enable the visit forms.
"""

from datetime import date
from http import HTTPStatus

import pytest
from dateutil.relativedelta import relativedelta
from django.urls import reverse

from project.constants.user import AUDIT_CENTRE_EDITOR, RCPCH_AUDIT_TEAM
from project.npda.general_functions.audit_period import get_audit_period_for_date
from project.npda.models.audit_period import AuditPeriod
from project.npda.models.npda_user import NPDAUser
from project.npda.models.paediatric_diabetes_unit import PaediatricDiabetesUnit
from project.npda.models.transfer import Transfer
from project.npda.tests.constants_for_tests import ALDER_HEY_PZ_CODE
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.factories.visit_factory import VisitFactory
from project.npda.tests.utils import create_submission, login_and_verify_user

UNLOCK_BUTTON_TEXT = "Unlock (Audit Team only)"


def create_transfer_patient_with_visit():
    """
    Create a patient who left Alder Hey during the current audit period,
    in a questionnaire (non-CSV) submission, with one visit.

    Returns (patient, visit, audit_period).
    """
    # is_in_transfer_in_the_last_year derives its window from today, so the
    # audit period used must be the one covering today
    start_date, end_date = get_audit_period_for_date(date.today())
    audit_period = AuditPeriod.objects.get(start_date=start_date, end_date=end_date)

    submission = create_submission(audit_period, ALDER_HEY_PZ_CODE)

    patient = PatientFactory(is_valid=True)
    submission.patients.add(patient)

    transfer = Transfer.objects.get(patient=patient)
    # Point the transfer at Alder Hey so PDU permission checks pass for
    # non-audit-team users
    transfer.paediatric_diabetes_unit = PaediatricDiabetesUnit.objects.get(
        pz_code=ALDER_HEY_PZ_CODE
    )
    transfer.date_leaving_service = audit_period.start_date + relativedelta(days=2)
    transfer.save()

    assert patient.is_in_transfer_in_the_last_year()

    visit = VisitFactory(
        patient=patient,
        visit_date=audit_period.start_date + relativedelta(days=1),
    )

    return patient, visit, audit_period


def get_user(role):
    return NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
        role=role,
    ).first()


def patient_update_url(audit_period, patient):
    return reverse(
        "pdu-patient-update",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
            "pk": patient.pk,
        },
    )


def visit_update_url(audit_period, patient, visit):
    return reverse(
        "pdu-visit-update",
        kwargs={
            "audit_period": audit_period.slug,
            "pz_code": ALDER_HEY_PZ_CODE,
            "patient_id": patient.pk,
            "pk": visit.pk,
        },
    )


def visit_date_input_html(response):
    """Return the rendered HTML of the visit date input (a single line)."""
    return next(
        line
        for line in response.content.decode().splitlines()
        if 'id="id_visit_date"' in line
    )


@pytest.mark.django_db
def test_audit_team_sees_unlock_button_for_patient_in_transfer(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    patient, _, audit_period = create_transfer_patient_with_visit()

    client = login_and_verify_user(client, get_user(RCPCH_AUDIT_TEAM))

    response = client.get(patient_update_url(audit_period, patient))

    assert response.status_code == HTTPStatus.OK
    assert UNLOCK_BUTTON_TEXT in response.content.decode()


@pytest.mark.django_db
def test_audit_team_sees_unlock_button_for_patient_in_transfer_on_visit_form(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    patient, visit, audit_period = create_transfer_patient_with_visit()

    client = login_and_verify_user(client, get_user(RCPCH_AUDIT_TEAM))

    response = client.get(visit_update_url(audit_period, patient, visit))

    assert response.status_code == HTTPStatus.OK
    assert UNLOCK_BUTTON_TEXT in response.content.decode()


@pytest.mark.django_db
def test_non_audit_team_user_does_not_see_unlock_button_for_patient_in_transfer(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    patient, _, audit_period = create_transfer_patient_with_visit()

    client = login_and_verify_user(client, get_user(AUDIT_CENTRE_EDITOR))

    response = client.get(patient_update_url(audit_period, patient))

    assert response.status_code == HTTPStatus.OK
    assert UNLOCK_BUTTON_TEXT not in response.content.decode()
    # The transfer banner is still shown
    assert (
        "This patient has been transferred in the last year."
        in response.content.decode()
    )


@pytest.mark.django_db
def test_visit_form_locked_for_patient_in_transfer_without_unlock(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    patient, visit, audit_period = create_transfer_patient_with_visit()

    client = login_and_verify_user(client, get_user(RCPCH_AUDIT_TEAM))

    response = client.get(visit_update_url(audit_period, patient, visit))

    assert response.status_code == HTTPStatus.OK
    assert "pointer-events-none" in visit_date_input_html(response)


@pytest.mark.django_db
def test_visit_form_unlocked_for_patient_in_transfer_with_unlock(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    patient, visit, audit_period = create_transfer_patient_with_visit()

    client = login_and_verify_user(client, get_user(RCPCH_AUDIT_TEAM))

    response = client.get(
        visit_update_url(audit_period, patient, visit) + "?unlock=true"
    )

    assert response.status_code == HTTPStatus.OK
    assert "pointer-events-none" not in visit_date_input_html(response)
    # Already unlocked: the button is replaced by the unlocked banner message
    assert UNLOCK_BUTTON_TEXT not in response.content.decode()
