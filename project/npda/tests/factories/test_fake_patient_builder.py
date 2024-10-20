"""Tests related to generating fake Patient instances"""

from datetime import date
import pytest

from project.npda.general_functions.data_generator_extended import FakePatientCreator
from project.npda.tests.factories.patient_factory import PatientFactory, AgeRange


@pytest.mark.django_db
def test_patient_factory_creation():
    """Test Patient Factory creation."""

    DATE_IN_AUDIT = date(2024, 4, 1)
    fake_patient_creator = FakePatientCreator(date_in_audit=DATE_IN_AUDIT)

    new_pts = fake_patient_creator.create_and_save_fake_patients(
        n=100,
        age_range=AgeRange.AGE_0_4,
    )

    for i in new_pts:
        print(i.age)
        print([v.visit_date for v in i.visit_set.all()])
        print()
