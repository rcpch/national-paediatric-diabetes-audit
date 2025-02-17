import pytest

from django.urls import reverse
from http import HTTPStatus

from project.constants.user import RCPCH_AUDIT_TEAM
from project.npda.models import Patient, Submission, NPDAUser
from project.npda.tests.utils import login_and_verify_user
from project.npda.tests.factories.patient_factory import PatientFactory


GOSH_PZ_CODE = "PZ196"
ALDER_HEY_PZ_CODE = "PZ074"


def create_submission_with_patient(user):
    submission = Submission.objects.create(
        audit_year=2024,
        submission_date="2024-04-01",
        submission_active=True,
        submission_by=user,
        paediatric_diabetes_unit=user.organisation_employers.first(),
    )

    patient = PatientFactory()
    submission.patients.add(patient)

    return patient


def get_patient_list(client):
    url = reverse("patients")
    response = client.get(url)

    assert response.status_code == HTTPStatus.OK

    return response.context_data["object_list"]


def set_view_preference(client, pz_code):
    url = reverse("view_preference")
    params = {
        "view_preference": 1,
        "pz_code_select_name": pz_code
    }

    response = client.post(url, params, headers={"HX-Request": "true"})
    assert response.status_code == HTTPStatus.NO_CONTENT    


@pytest.mark.django_db
def test_users_can_only_see_patients_from_their_pdu(
    seed_groups_fixture,
    seed_users_fixture,
    client,
):
    """Except for RCPCH_AUDIT_TEAM, users should only see patients from their own PDU."""

    gosh_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=GOSH_PZ_CODE
    ).first()

    ah_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    ).first()

    gosh_patient = create_submission_with_patient(gosh_user)
    ah_patient = create_submission_with_patient(ah_user)

    client = login_and_verify_user(client, ah_user)
    patients = get_patient_list(client)
    
    assert(len(patients) == 1)
    assert(patients.first().pk == ah_patient.pk)


@pytest.mark.django_db
def test_rcpch_audit_team_can_see_patients_from_all_pdus(
    seed_groups_fixture,
    seed_users_fixture,
    client,
):
    gosh_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=GOSH_PZ_CODE
    ).first()

    ah_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    ).first()

    rcpch_user = NPDAUser.objects.filter(
        is_rcpch_audit_team_member=True
    ).first()

    gosh_patient = create_submission_with_patient(gosh_user)
    ah_patient = create_submission_with_patient(ah_user)

    client = login_and_verify_user(client, rcpch_user)

    # GOSH
    set_view_preference(client, GOSH_PZ_CODE)
    patients = get_patient_list(client)
    
    assert(len(patients) == 1)
    assert(patients.first().pk == gosh_patient.pk)

    # Alder Hey
    set_view_preference(client, ALDER_HEY_PZ_CODE)
    patients = get_patient_list(client)
    
    assert(len(patients) == 1)
    assert(patients.first().pk == ah_patient.pk)
