"""Tests related to generating fake Patient instances"""
import pytest

from project.npda.tests.factories.patient_factory import PatientFactory, AgeRange

@pytest.mark.django_db
def test_patient_factory_creation():
    """Test Patient Factory creation."""

    for _ in range(10):
        pt = PatientFactory.build(age_range=AgeRange.AGE_11_15)

        print(f"{pt.sex=}")
        print(f"{pt.age()=}")
        # print(f"{pt.audit_start_date=}")
        print(f"{pt.diagnosis_date=}")
        print("")