"""Performance testing views"""

from datetime import date
import time

import pytest
from project.npda.general_functions.data_generator_extended import (
    AgeRange,
    FakePatientCreator,
    HbA1cTargetRange,
    VisitType,
)
from freezegun import freeze_time

from project.npda.models.npda_user import NPDAUser
from project.npda.models.submission import Submission
from project.npda.tests.test_csv_upload import ALDER_HEY_PZ_CODE
from project.npda.tests.utils import login_and_verify_user
import logging

# Logging
logger = logging.getLogger(__name__)


@pytest.mark.django_db
def test_dashboard_view_response_time(
    AUDIT_START_DATE,
    AUDIT_END_DATE,
    seed_groups_fixture,
    seed_users_fixture,
    seed_patients_fixture,
    client,
):
    """Basic performance test for the dashboard view response time with lots of patients.

    NOTE: this view uses many HTMX async requests for each viz's partial, so this test only checks the initial load time of the overall view.
    """

    N_PATIENTS = 100
    UPPERBOUND_LOAD_TIME_SECONDS = 1

    # First get user
    ah_user = NPDAUser.objects.filter(
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    ).first()

    # Login
    client = login_and_verify_user(client, ah_user)

    # Now create patients
    fake_patient_creator = FakePatientCreator(
        audit_start_date=AUDIT_START_DATE,
        audit_end_date=AUDIT_END_DATE,
    )
    new_pts = fake_patient_creator.create_and_save_fake_patients(
        n=N_PATIENTS,
        age_range=AgeRange.AGE_11_15,
        hb1ac_target_range=HbA1cTargetRange.TARGET,
        visit_types=[
            VisitType.CLINIC,
            VisitType.CLINIC,
            VisitType.ANNUAL_REVIEW,
            VisitType.DIETICIAN,
        ],
        visit_kwargs={"is_valid": True},
    )

    new_submission = Submission.objects.create(
        paediatric_diabetes_unit=ah_user.organisation_employers.first(),
        audit_year=AUDIT_START_DATE.year,
        submission_date=AUDIT_START_DATE,
        submission_by=ah_user,
        submission_active=True,
    )

    # Add patients to submission
    new_submission.patients.add(*new_pts)

    # GET the view
    start_time = time.time()
    response = client.get("/dashboard")
    end_time = time.time()
    response_time = end_time - start_time

    # Check valid response within some leeway upperbound
    assert response.status_code == 200
    assert response_time < UPPERBOUND_LOAD_TIME_SECONDS
    logger.info(f"Dashboard view response time for {N_PATIENTS=} is {response_time} seconds")
