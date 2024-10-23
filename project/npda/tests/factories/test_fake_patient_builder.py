"""Tests related to generating fake Patient instances"""

from datetime import date, timedelta
import random
import pytest
import time

from project.npda.general_functions.audit_period import (
    get_audit_period_for_date,
    get_quarter_for_visit,
)
from project.npda.general_functions.data_generator_extended import (
    FakePatientCreator,
    VisitType,
)
from project.npda.models.patient import Patient
from project.npda.tests.factories.patient_factory import (
    PatientFactory,
    AgeRange,
)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "age_range_enum",
    [
        AgeRange.AGE_0_4,
        AgeRange.AGE_5_10,
        AgeRange.AGE_11_15,
        AgeRange.AGE_16_19,
        AgeRange.AGE_20_25,
    ],
)
def test_fake_patient_creator_ages_all_appropriate(age_range_enum):
    """Tests that the ages of all fake patients fall into the appropriate
    age range.
    """

    DATE_IN_AUDIT = date(2024, 4, 1)
    audit_start_date, audit_end_date = get_audit_period_for_date(DATE_IN_AUDIT)
    fake_patient_creator = FakePatientCreator(
        audit_start_date=audit_start_date,
        audit_end_date=audit_end_date,
    )

    # Create patients within the specified age range
    new_pts = fake_patient_creator.create_and_save_fake_patients(
        n=5,
        age_range=age_range_enum,
        visit_types=[
            VisitType.CLINIC,
            VisitType.CLINIC,
            VisitType.CLINIC,
            VisitType.CLINIC,
            VisitType.DIETICIAN,
            VisitType.DIETICIAN,
            VisitType.DIETICIAN,
            VisitType.DIETICIAN,
            VisitType.ANNUAL_REVIEW,
            VisitType.CLINIC,
            VisitType.CLINIC,
            VisitType.CLINIC,
            VisitType.CLINIC,
        ],
    )

    # PRINT FOR DEBUGGING
    # patients = Patient.objects.prefetch_related("visit_set").all()
    # for patient in patients:
    #     print(f"Patient PK: {patient.pk}")
    #     for visit in patient.visit_set.all().order_by("visit_date"):
    #         print(f"Visit: {visit} (Q{get_quarter_for_visit(visit.visit_date)})")
    #     print()

    # Get the min and max of the current AgeRange enum
    min_age, max_age = age_range_enum.value

    # Calculate boundary dates for filtering patients
    audit_start = fake_patient_creator.audit_start_date
    max_age_boundary = audit_start - timedelta(days=365 * max_age)
    min_age_boundary = audit_start - timedelta(days=365 * min_age)

    # Filter patients whose date_of_birth falls within the boundaries of the current age range
    pts = Patient.objects.filter(
        date_of_birth__lte=min_age_boundary, date_of_birth__gt=max_age_boundary
    )

    # Verify each patient's age in days is within the specified range
    for pt in pts:
        # Get the age in days
        patient_age_days = pt.age_days(today_date=DATE_IN_AUDIT)

        # Convert age in days to years by dividing by 365.25
        patient_age_years = patient_age_days / 365.25

        # Assert the age in years falls within the given range
        assert (
            min_age <= patient_age_years <= max_age
        ), f"Patient {pt.id} is out of the age range: {patient_age_years:.2f} years"


# pytest project/npda/tests/factories/test_fake_patient_builder.py::test_performance_check_for_fake_patient_creator
@pytest.mark.skip(reason="Just a test for performance checking")
@pytest.mark.django_db
@pytest.mark.parametrize("n_patients_to_make", [10, 100, 1000, 10000])
def test_performance_check_for_fake_patient_creator(
    n_patients_to_make: int,
):
    """Test the performance of creating a large number of fake patients

    Creates lots of patients and visits. Each Patient has 12 visits.

       e53678bf8c8f34239a2669015763d41a0b2dc096
    +-------------------------+------------------+
    | Number of Patients       | Time (seconds)  |
    +-------------------------+------------------+
    | 10                      | 0.07             |
    | 100                     | 0.95             |
    | 1000                    | 8.72             |
    | 10000                   | 86.75            |
    +-------------------------+------------------+
    """

    N_VISITS_PER_PATIENT = 12

    # Generate visit types - randomly choose between clinic / dietician and
    # finally 1 annual review
    visit_types = [
        random.choice(
            [
                VisitType.CLINIC,
                VisitType.DIETICIAN,
            ]
        )
        for _ in range(N_VISITS_PER_PATIENT - 1)
    ] + [VisitType.ANNUAL_REVIEW]

    DATE_IN_AUDIT = date(2024, 4, 1)
    audit_start_date, audit_end_date = get_audit_period_for_date(DATE_IN_AUDIT)

    fake_patient_creator = FakePatientCreator(
        audit_start_date=audit_start_date,
        audit_end_date=audit_end_date,
    )

    # Dictionary to store time results
    time_results = {}
    # Start timing
    start_time = time.time()

    for age_range in AgeRange:
        # Create patients within the specified age range
        new_pts = fake_patient_creator.create_and_save_fake_patients(
            n=n_patients_to_make // len(AgeRange),
            age_range=age_range,
            visit_types=visit_types,
        )

    end_time = time.time()  # End timing
    elapsed_time = end_time - start_time

    # Store the result
    time_results[n_patients_to_make] = elapsed_time

    # After all the tests, print the table
    if n_patients_to_make == 10000:  # After the last test case
        print("\n+-------------------------+------------------+")
        print("| Number of Patients       | Time (seconds)   |")
        print("+-------------------------+------------------+")
        for patients, time_taken in time_results.items():
            print(f"| {patients:<23} | {time_taken:<16.2f} |")
        print("+-------------------------+------------------+")
