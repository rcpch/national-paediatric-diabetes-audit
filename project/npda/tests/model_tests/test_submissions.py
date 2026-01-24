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
from datetime import date, timedelta

# Python imports
import pytest

# 3rd party imports
from django.urls import reverse
from django.utils import timezone
from django.apps import apps

from project.constants.user import RCPCH_AUDIT_TEAM

# NPDA imports
from project.npda.models import NPDAUser, Submission, Transfer, AuditPeriod
from project.npda.tests.utils import login_and_verify_user
from project.npda.tests.factories import (
    PatientFactory,
    PaediatricsDiabetesUnitFactory,
    NPDAUserFactory,
)
from project.npda.general_functions import audit_period

logger = logging.getLogger(__name__)

ALDER_HEY_PZ_CODE = "PZ074"
ALDER_HEY_ODS_CODE = "RBS25"

GOSH_PZ_CODE = "PZ196"
GOSH_ODS_CODE = "RP401"

audit_dates = audit_period.get_audit_period_for_date(date.today())


@pytest.mark.django_db
def test_npda_user_can_create_submission(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
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
        audit_year=audit_dates[0].year,
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
def test_npda_user_cannot_submit_same_patient_twice_within_the_same_submission(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    """Test NPDAUser cannot submit the same patient twice in the same submission in the same PDU."""

    # Get Alder Hey user from fixture
    ah_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    ).first()

    Submission.objects.all().delete()  # Clear any existing submissions

    # Login as Alder Hey user
    client = login_and_verify_user(client, ah_user)

    # Get Alder Hey PDU
    pdu = PaediatricsDiabetesUnitFactory(pz_code=ALDER_HEY_PZ_CODE)

    # Create a submission
    new_submission = Submission.objects.create(
        paediatric_diabetes_unit=pdu,
        audit_year=audit_dates[0].year,
        submission_date=timezone.now(),
        submission_by=ah_user,  # user is the user who is logged in. Passed in as a parameter
        submission_active=True,
    )

    submission_last_audit_year = Submission.objects.create(
        paediatric_diabetes_unit=pdu,
        audit_year=audit_dates[0].year - 1,
        submission_date=timezone.now(),
        submission_by=ah_user,  # user is the user who is logged in. Passed in as a parameter
        submission_active=True,
    )

    # Create a patient
    patient = PatientFactory()

    # Add patient to previous year's submission
    submission_last_audit_year.patients.add(patient)

    # Add patient to submission
    new_submission.patients.add(patient)

    # Try to add the same patient to this year's submission a second time
    new_submission.patients.add(patient)

    # Check patient was not added to submission twice
    assert new_submission.patients.count() == 1
    assert patient in new_submission.patients.all()
    assert new_submission.patients.filter(pk=patient.pk).count() == 1
    assert (  # There should be only one submission for the patient in this audit year and PDU
        Submission.objects.filter(
            audit_year=audit_dates[0].year, paediatric_diabetes_unit=pdu
        ).count()
        == 1
    )
    # This patient should be in the previous year's submission as well as this year's submission
    assert Submission.objects.filter(paediatric_diabetes_unit=pdu).count() == 2


@pytest.mark.django_db
def test_npda_user_can_submit_same_patient_twice_within_the_same_submission_in_different_pdus(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    """Test NPDAUser cannot submit the same patient twice in the same submission in different PDUs."""

    # Get Alder Hey user from fixture
    ah_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    ).first()
    gos_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=GOSH_PZ_CODE
    ).first()

    # Login as Alder Hey user
    client = login_and_verify_user(client, ah_user)

    # Get Alder Hey PDU
    alderhey_pdu = PaediatricsDiabetesUnitFactory(pz_code=ALDER_HEY_PZ_CODE)
    gos_pdu = PaediatricsDiabetesUnitFactory(pz_code=GOSH_PZ_CODE)

    # Create a submission
    new_alderhey_submission = Submission.objects.create(
        paediatric_diabetes_unit=alderhey_pdu,
        audit_year=audit_dates[0].year,
        submission_date=timezone.now(),
        submission_by=ah_user,  # user is the user who is logged in. Passed in as a parameter
        submission_active=True,
    )

    new_gosh_submission = Submission.objects.create(
        paediatric_diabetes_unit=gos_pdu,
        audit_year=audit_dates[0].year,
        submission_date=timezone.now(),
        submission_by=gos_user,  # user is not logged in
        submission_active=True,
    )

    # Create a patient
    patient = PatientFactory()

    # Add patient to submission
    new_alderhey_submission.patients.add(patient)

    # Check patient was not added to submission twice
    assert new_alderhey_submission.patients.count() == 1
    assert patient in new_alderhey_submission.patients.all()
    assert new_alderhey_submission.patients.filter(pk=patient.pk).count() == 1
    assert (  # There should be only one submission for the patient in this audit year and PDU
        Submission.objects.filter(
            audit_year=audit_dates[0].year, paediatric_diabetes_unit=alderhey_pdu
        ).count()
        == 1
    )

    assert new_gosh_submission.patients.count() == 0

    # Try to add the same patient to GOSH submission
    # asset an error was raised trying this
    # with pytest.raises(Exception):
    #     new_gosh_submission.patients.add(patient)
    new_gosh_submission.patients.add(patient)

    PatientSubmission = apps.get_model(app_label="npda", model_name="PatientSubmission")
    # Check there are two submissions for the patient in this audit year
    assert (
        PatientSubmission.objects.filter(
            patient=patient, submission__submission_active=True
        ).count()
        == 2
    )

    assert new_gosh_submission.patients.count() == 1
    assert patient in new_gosh_submission.patients.all()
    assert new_gosh_submission.patients.filter(pk=patient.pk).count() == 1
    assert (  # There should be only one submission for the patient in this audit year and PDU
        Submission.objects.filter(
            audit_year=audit_dates[0].year, paediatric_diabetes_unit=gos_pdu
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_patients_copied_from_previous_questionnaire_submission(
    seed_groups_fixture,
    seed_users_fixture,
    seed_audit_periods_fixture,
    client,
):
    ah_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE
    ).first()

    client = login_and_verify_user(client, ah_user)

    pdu = PaediatricsDiabetesUnitFactory(pz_code=ALDER_HEY_PZ_CODE)

    current_audit_period = AuditPeriod.objects.get(start_date__year=2025)
    previous_audit_period = current_audit_period.previous_audit_period()

    previous_submission = Submission.objects.create(
        paediatric_diabetes_unit=pdu,
        audit_year=previous_audit_period.audit_year(),
        audit_period=previous_audit_period,
        submission_date=previous_audit_period.end_date - timedelta(days=1),
        submission_by=ah_user,
        submission_active=True,
    )

    # Patient 1: Normal patient (should be copied)
    patient_1 = PatientFactory()
    previous_submission.patients.add(patient_1)

    # Patient 2: Patient with left service (should NOT be copied)
    patient_2 = PatientFactory()
    previous_submission.patients.add(patient_2)
    Transfer.objects.create(
        patient=patient_2,
        paediatric_diabetes_unit=pdu,
        date_leaving_service=previous_audit_period.end_date - timedelta(days=1),
        reason_leaving_service=1,  # Transitioned to adult diabetes service
    )

    # Patient 3: Patient with death date (should NOT be copied)
    patient_3 = PatientFactory(death_date=previous_audit_period.end_date - timedelta(days=1))
    previous_submission.patients.add(patient_3)
    Transfer.objects.create(
        patient=patient_3,
        paediatric_diabetes_unit=pdu,
    )

    assert previous_submission.patients.count() == 3

    assert False, "TODO MRB: New endpoint not implemented yet"

    # Call the pdu-patient-add endpoint for the next audit period
    # from project.npda.forms.patient_form import PatientForm

    # # Create a new patient using valid fields
    # new_patient_form = PatientForm(
    #     {
    #         "nhs_number": "1111111234",
    #         "sex": 1,
    #         "date_of_birth": date(2010, 1, 1),
    #         "postcode": "B11 4BH",
    #         "ethnicity": "A",
    #         "diabetes_type": 1,
    #         "diagnosis_date": date(2015, 1, 1),
    #     },
    #     paediatric_diabetes_unit=pdu,
    #     audit_period=next_audit_period,
    # )

    # assert new_patient_form.is_valid(), f"Form errors: {new_patient_form.errors}"

    # # Post to the pdu-patient-add endpoint for next audit period
    # url = reverse(
    #     "pdu-patient-add",
    #     kwargs={"audit_period": next_audit_period.slug, "pz_code": ALDER_HEY_PZ_CODE},
    # )

    # response = client.post(url, new_patient_form.data)

    # # Check that the redirect was successful (patient was created)
    # assert response.status_code == 302

    # # Verify a submission was created for the next audit period
    # next_submission = Submission.objects.filter(
    #     audit_year=next_audit_period.audit_year(),
    #     paediatric_diabetes_unit=pdu,
    #     submission_active=True,
    # ).first()

    # assert next_submission is not None

    # # Verify that ONLY patient_1 (the normal patient without leaving/death data) was copied
    # assert next_submission.patients.count() == 2  # The new patient + patient_1
    # assert patient_1 in next_submission.patients.all()
    # assert patient_2 not in next_submission.patients.all()
    # assert patient_3 not in next_submission.patients.all()
