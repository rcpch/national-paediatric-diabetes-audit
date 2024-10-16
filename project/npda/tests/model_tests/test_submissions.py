"""
This file contains tests for the submissions model and views.

Model classes tested:
- Only one submissions for a PDU & ODS code in the session for a given audit year/quarter should be active

View classes tested:
 -  SubmissionsListView GET request should return all submissions for the PDU & ODS code in the session for all audit years/quarters
 -  SubmissionsListView GET request should NOT return the active submissions for a PDU & ODS code not in the session for all audit years/quarters
- SubmissionsListView POST request with param "submit-data" of value "delete-data" should delete the submission for the PDU & ODS code in the session
- SubmissionsListView POST request with param "submit-data" of value "delete-data" should NOT delete the submission for a different PDU & ODS code to that in the session
- SubmissionsListView POST request with param "submit-data" of value "delete-data" should NOT delete the submission for the PDU & ODS code in the session if the submission is not active
"""

from http import HTTPStatus
import logging
from datetime import date

# Python imports
import pytest

# 3rd party imports
from django.urls import reverse
from django.utils import timezone

from project.constants.user import RCPCH_AUDIT_TEAM

# NPDA imports
from project.npda.models import NPDAUser, Submission
from project.npda.tests.utils import login_and_verify_user
from project.npda.tests.factories import PatientFactory, PaediatricsDiabetesUnitFactory

logger = logging.getLogger(__name__)

ALDER_HEY_PZ_CODE = "PZ074"
ALDER_HEY_ODS_CODE = "RBS25"

GOSH_PZ_CODE = "PZ196"
GOSH_ODS_CODE = "RP401"


@pytest.mark.django_db
def test_npda_user_can_create_submission(
    seed_groups_fixture,
    seed_patients_fixture,
    client,
):
    """Test NPDAUser can create a submission for their PDU code."""

    # Get Alder Hey user from fixture
    ah_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    ).first()

    # Login as Alder Hey user

    client = login_and_verify_user(client, ah_user)

    # Get Alder Hey PDU
    pdu = PaediatricsDiabetesUnitFactory(pz_code=ALDER_HEY_PZ_CODE)

    # Create some patients
    patients = PatientFactory.create_batch(5)

    # Create a submission
    new_submission = Submission.objects.create(
        paediatric_diabetes_unit=pdu,
        audit_year=date.today().year,
        submission_date=timezone.now(),
        submission_by=ah_user,  # user is the user who is logged in. Passed in as a parameter
        submission_active=True,
    )

    # Add patients to submission
    new_submission.patients.add(*patients)

    # Check submission was created
    assert new_submission is not None
    assert new_submission in Submission.objects.all()
    # assert new_submission in ah_user.submissions.all()
    assert new_submission in pdu.pdu_submissions.all()
    assert new_submission.patients.count() == 5


@pytest.mark.django_db
def test_npda_user_cannot_submit_same_patient_twice(
    seed_groups_fixture,
    seed_patients_fixture,
    client,
):
    """Test NPDAUser cannot submit the same patient twice in the same submission."""

    # Get Alder Hey user from fixture
    ah_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    ).first()

    # Login as Alder Hey user
    client = login_and_verify_user(client, ah_user)

    # Get Alder Hey PDU
    pdu = PaediatricsDiabetesUnitFactory(pz_code=ALDER_HEY_PZ_CODE)

    pdu_2 = PaediatricsDiabetesUnitFactory(pz_code="PZ999")

    # Create a submission
    new_submission = Submission.objects.create(
        paediatric_diabetes_unit=pdu,
        audit_year=date.today().year,
        submission_date=timezone.now(),
        submission_by=ah_user,  # user is the user who is logged in. Passed in as a parameter
        submission_active=True,
    )

    another_submission = Submission.objects.create(
        paediatric_diabetes_unit=pdu_2,
        audit_year=date.today().year,
        submission_date=timezone.now(),
        submission_by=ah_user,  # user is the user who is logged in. Passed in as a parameter
        submission_active=True,
    )

    # Create a patient
    patient = PatientFactory()

    # Add patient to submission
    new_submission.patients.add(patient)

    # Try to add the same patient to the submission
    another_submission.patients.add(patient)

    # Check patient was not added to submission
    assert new_submission.patients.count() == 1
    assert another_submission.patients.count() == 0
