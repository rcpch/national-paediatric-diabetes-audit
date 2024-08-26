"""Tests for the CalculateKPIS class."""

from datetime import date, timedelta
import logging
from typing import List
import pytest

from project.npda.general_functions.kpis import CalculateKPIS
from project.npda.general_functions.model_utils import print_instance_field_attrs
from project.npda.models import Patient, Visit
from project.npda.tests.factories.patient_factory import PatientFactory

# Logging
logger = logging.getLogger(__name__)


@pytest.fixture
def TODAY():
    """TODAY is Day 2 of the first audit period"""
    return date(year=2024, month=4, day=2)


def test_ensure_mocked_audit_date_range_is_correct(TODAY):
    """Ensure that the mocked audit date range is correct."""
    calc_kpis = CalculateKPIS(pz_code="mocked_pz_code", calculation_date=TODAY)

    assert calc_kpis.audit_start_date == date(
        2024, 4, 1
    ), f"Mocked audit start date incorrect!"
    assert calc_kpis.audit_end_date == date(
        2025, 3, 31
    ), f"Mocked audit end date incorrect!"


@pytest.mark.django_db
def test_kpi_calculation_1(TODAY):
    """Tests that KPI1 is calculated correctly."""

    # Ensure starting with clean pts in test db
    Patient.objects.all().delete()

    # Create Patients and Visits that should PASS KPI1
    passing_patients: List[Patient] = PatientFactory.create_batch(size=5)

    for pt in passing_patients:

        # Access the related visit(s)
        visits = pt.visit_set.all()

        if visits.count() > 1:
            assert False, "Only one visit should be created for each patient."

        visit = visits.first()
        # Set visit date to TODAY plus 1 day
        visit.visit_date = TODAY + timedelta(days=1)
        visit.save()

        print(f"{Visit.objects.filter(patient=pt).values_list()=}")
    # CalculateKPIS(pz_code=)

    assert False
