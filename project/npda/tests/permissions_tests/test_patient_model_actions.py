import pytest

from django.urls import reverse
from django.utils.timezone import make_aware
from http import HTTPStatus

from project.constants.user import RCPCH_AUDIT_TEAM
from project.npda.models import Patient, Submission, NPDAUser
from project.npda.tests.utils import login_and_verify_user
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.factories.visit_factory import VisitFactory


GOSH_PZ_CODE = "PZ196"
ALDER_HEY_PZ_CODE = "PZ074"


def create_submission_with_patient(user):
    submission = Submission.objects.create(
        audit_year=2024,
        submission_date="2024-04-01T00:00:00Z",
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


def set_view_preference(client, view_preference, pz_code):
    url = reverse("view_preference")
    params = {
        "view_preference": view_preference,
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
    set_view_preference(client, view_preference=1, pz_code=GOSH_PZ_CODE)
    patients = get_patient_list(client)
    
    assert(len(patients) == 1)
    assert(patients.first().pk == gosh_patient.pk)

    # Alder Hey
    set_view_preference(client, view_preference=1, pz_code=ALDER_HEY_PZ_CODE)
    patients = get_patient_list(client)
    
    assert(len(patients) == 1)
    assert(patients.first().pk == ah_patient.pk)


@pytest.mark.django_db
def test_rcpch_audit_team_can_see_all_patients(
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

    set_view_preference(client, view_preference=2, pz_code=GOSH_PZ_CODE)
    patients = get_patient_list(client)
    
    assert(len(patients) == 2)
    
    pks = [patient.pk for patient in patients]
    assert(gosh_patient.pk in pks)
    assert(ah_patient.pk in pks)


@pytest.mark.django_db
def test_users_can_only_edit_patients_from_their_own_pdu(
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

    ah_patient = create_submission_with_patient(ah_user)

    client = login_and_verify_user(client, gosh_user)

    url = reverse("patient-update", args=[ah_patient.pk])
    response = client.get(url)

    assert(response.status_code == HTTPStatus.FORBIDDEN)


@pytest.mark.django_db
def test_rcpch_audit_team_can_edit_patients_from_any_pdu(
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

    gosh_url = reverse("patient-update", args=[gosh_patient.pk])
    assert(client.get(gosh_url).status_code == HTTPStatus.OK)

    ah_url = reverse("patient-update", args=[ah_patient.pk])
    assert(client.get(ah_url).status_code == HTTPStatus.OK)


@pytest.mark.django_db
def test_users_can_only_see_patient_visits_from_their_own_pdu(
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

    ah_patient = create_submission_with_patient(ah_user)

    client = login_and_verify_user(client, gosh_user)

    url = reverse("patient_visits", args=[ah_patient.pk])
    response = client.get(url)

    assert(response.status_code == HTTPStatus.FORBIDDEN)


@pytest.mark.django_db
def test_rcpch_audit_team_can_see_visits_from_all_pdus(
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

    gosh_url = reverse("patient_visits", args=[gosh_patient.pk])
    assert(client.get(gosh_url).status_code == HTTPStatus.OK)

    ah_url = reverse("patient_visits", args=[ah_patient.pk])
    assert(client.get(ah_url).status_code == HTTPStatus.OK)


@pytest.mark.django_db
def test_users_can_only_edit_patient_visits_from_their_own_pdu(
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

    ah_patient = create_submission_with_patient(ah_user)
    ah_visit = VisitFactory(patient=ah_patient)

    client = login_and_verify_user(client, gosh_user)

    url = reverse("visit-update", args=[ah_patient.pk, ah_visit.pk])
    response = client.get(url)

    assert(response.status_code == HTTPStatus.FORBIDDEN)


@pytest.mark.django_db
def test_rcpch_audit_team_can_edit_visits_from_all_pdus(
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
    gosh_visit = VisitFactory(patient=gosh_patient)

    ah_patient = create_submission_with_patient(ah_user)
    ah_visit = VisitFactory(patient=ah_patient)

    client = login_and_verify_user(client, rcpch_user)

    gosh_url = reverse("visit-update", args=[gosh_patient.pk, gosh_visit.pk])
    assert(client.get(gosh_url).status_code == HTTPStatus.OK)

    ah_url = reverse("visit-update", args=[ah_patient.pk, ah_visit.pk])
    assert(client.get(ah_url).status_code == HTTPStatus.OK)