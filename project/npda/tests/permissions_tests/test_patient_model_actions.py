import pytest

from django.urls import reverse
from http import HTTPStatus

from project.constants.user import RCPCH_AUDIT_TEAM
from project.npda.models import Patient, Submission, NPDAUser
from project.npda.tests.utils import login_and_verify_user
from project.npda.tests.factories.patient_factory import PatientFactory


GOSH_PZ_CODE = "PZ196"
ALDER_HEY_PZ_CODE = "PZ074"


@pytest.mark.django_db
def test_npda_user_list_view_users_can_only_see_patients_from_their_pdu(
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

    gosh_submission = Submission.objects.create(
        audit_year=2024,
        submission_date="2024-04-01",
        submission_active=True,
        submission_by=gosh_user,
        paediatric_diabetes_unit=gosh_user.organisation_employers.first(),
    )

    gosh_patient = PatientFactory()
    gosh_submission.patients.add(gosh_patient)

    ah_submission = Submission.objects.create(
        audit_year=2024,
        submission_date="2024-04-01",
        submission_active=True,
        submission_by=ah_user,
        paediatric_diabetes_unit=ah_user.organisation_employers.first(),
    )

    ah_patient = PatientFactory()
    ah_submission.patients.add(ah_patient)

    client = login_and_verify_user(client, ah_user)

    url = reverse("patients")
    response = client.get(url)

    assert response.status_code == HTTPStatus.OK

    patients = response.context_data["object_list"]
    
    assert(len(patients) == 1)
    assert(patients.first().pk == ah_patient.pk)

