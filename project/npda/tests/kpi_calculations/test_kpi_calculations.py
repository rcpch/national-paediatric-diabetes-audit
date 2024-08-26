"""Tests for the CalculateKPIS class."""

from datetime import date
import logging
import pytest

from project.npda.general_functions.kpis import CalculateKPIS
from project.npda.general_functions.model_utils import print_instance_field_attrs
from project.npda.models import Patient, Visit
from project.npda.tests.factories.patient_factory import PatientFactory

# Logging
logger = logging.getLogger(__name__)

@pytest.fixture
def TODAY():
    return date(year=2024,month=1, day=1)

@pytest.mark.django_db
def test_kpi_calculation_1(
    seed_groups_fixture,
    seed_users_fixture,
    TODAY
):
    """Tests that KPI1 is calculated correctly."""

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create Patients and Visits that should PASS KPI1
    
    passing_patients = PatientFactory.create_batch(size=5)
    
    print('passingpts\n\n')
    for pt in passing_patients:
        print_instance_field_attrs(pt)
        print(f"{pt.transfer=}")
    
    # CalculateKPIS(pz_code=)

    assert False
