import random
from datetime import timedelta
from decimal import Decimal

import pytest

from project.constants import DIABETES_TYPES, HBA1C_FORMATS
from project.npda.models import Visit
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.factories.visit_factory import VisitFactory
from project.npda.views.dashboard.patient_characteristics import (
    get_median_hba1c_by_patient,
)
from project.npda.general_functions.audit_period import audit_period_for_audit_year


@pytest.mark.django_db
class TestReturnEligibleVisits:
    @pytest.fixture
    def setup_patients_and_visits(self):
        # Create patients with different audit years
        audit_year = 2024
        audit_start, audit_end = audit_period_for_audit_year(audit_year)

        # Create patient with mmol/mol HbA1c format
        patient_mmol = PatientFactory(
            diabetes_type=DIABETES_TYPES[0][0],  # T1DM
            diagnosis_date=audit_start
            - timedelta(days=180),  # Diagnosed before audit period
            audit_start_date=audit_start,
            audit_end_date=audit_end,
        )

        # Create patient with percent HbA1c format
        patient_percent = PatientFactory(
            diabetes_type=DIABETES_TYPES[0][0],  # T1DM
            diagnosis_date=audit_start
            - timedelta(days=180),  # Diagnosed before audit period
            audit_start_date=audit_start,
            audit_end_date=audit_end,
        )

        # Remove auto-created visits (we'll create specific ones for testing)
        Visit.objects.filter(patient__in=[patient_mmol, patient_percent]).delete()

        # Create visits with specific HbA1c values and formats
        # Visit with mmol/mol format
        visit_mmol = VisitFactory(
            patient=patient_mmol,
            visit_date=audit_start + timedelta(days=random.randint(30, 150)),
            hba1c_date=audit_start + timedelta(days=random.randint(30, 150)),
            hba1c=Decimal("58.0"),
            hba1c_format=HBA1C_FORMATS[0][0],  # mmol/mol
        )

        # Visit with % format
        visit_percent = VisitFactory(
            patient=patient_percent,
            visit_date=audit_start + timedelta(days=random.randint(30, 150)),
            hba1c_date=audit_start + timedelta(days=random.randint(30, 150)),
            hba1c=Decimal("7.5"),
            hba1c_format=HBA1C_FORMATS[1][0],  # %
        )

        # Create a visit that should be excluded (too early after diagnosis)
        early_visit = VisitFactory(
            patient=patient_mmol,
            visit_date=patient_mmol.diagnosis_date + timedelta(days=15),
            hba1c_date=patient_mmol.diagnosis_date + timedelta(days=15),
            hba1c=Decimal("60.0"),
            hba1c_format=HBA1C_FORMATS[0][0],  # mmol/mol
        )

        # Create a visit with null HbA1c
        null_hba1c_visit = VisitFactory(
            patient=patient_mmol,
            visit_date=audit_start + timedelta(days=random.randint(30, 150)),
            hba1c_date=audit_start + timedelta(days=random.randint(30, 150)),
            hba1c=None,
            hba1c_format=HBA1C_FORMATS[0][0],  # mmol/mol
        )

        # Create patient and visit for previous audit year
        prev_audit_start, prev_audit_end = audit_period_for_audit_year(audit_year - 1)
        patient_prev_year = PatientFactory(
            diabetes_type=DIABETES_TYPES[0][0],  # T1DM
            diagnosis_date=prev_audit_start - timedelta(days=180),
            audit_start_date=prev_audit_start,
            audit_end_date=prev_audit_end,
        )
        Visit.objects.filter(patient=patient_prev_year).delete()

        visit_prev_year = VisitFactory(
            patient=patient_prev_year,
            visit_date=prev_audit_start + timedelta(days=random.randint(30, 150)),
            hba1c_date=prev_audit_start + timedelta(days=random.randint(30, 150)),
            hba1c=Decimal("55.0"),
            hba1c_format=HBA1C_FORMATS[0][0],  # mmol/mol
        )

        # Create patient and visit for next audit year
        next_audit_start, next_audit_end = audit_period_for_audit_year(audit_year + 1)
        patient_next_year = PatientFactory(
            diabetes_type=DIABETES_TYPES[0][0],  # T1DM
            diagnosis_date=next_audit_start - timedelta(days=180),
            audit_start_date=next_audit_start,
            audit_end_date=next_audit_end,
        )
        Visit.objects.filter(patient=patient_next_year).delete()

        visit_next_year = VisitFactory(
            patient=patient_next_year,
            visit_date=next_audit_start + timedelta(days=random.randint(30, 150)),
            hba1c_date=next_audit_start + timedelta(days=random.randint(30, 150)),
            hba1c=Decimal("52.0"),
            hba1c_format=HBA1C_FORMATS[0][0],  # mmol/mol
        )

        return {
            "patient_mmol": patient_mmol,
            "patient_percent": patient_percent,
            "patient_prev_year": patient_prev_year,
            "patient_next_year": patient_next_year,
            "visit_mmol": visit_mmol,
            "visit_percent": visit_percent,
            "early_visit": early_visit,
            "null_hba1c_visit": null_hba1c_visit,
            "visit_prev_year": visit_prev_year,
            "visit_next_year": visit_next_year,
            "audit_year": audit_year,
            "audit_start": audit_start,
            "audit_end": audit_end,
        }

    def test_mmol_mol_format_and_median_conversion(self, setup_patients_and_visits):
        """Test HbA1c values in mmol/mol format are correctly processed"""
        # Get the test data
        patient_data = setup_patients_and_visits
        patient_mmol = patient_data["patient_mmol"]
        audit_start, audit_end = audit_period_for_audit_year(patient_data["audit_year"])

        # Get visits using the function
        visits = get_median_hba1c_by_patient(
            audit_start=audit_start, audit_end=audit_end, patients=[patient_mmol]
        )
        visit_data = list(visits)

        # Assertions
        assert len(visit_data) == 1
        assert visit_data[0]["median_hba1c_mmol_mol"] == Decimal("58.0")

        # Calculate expected HbA1c percent conversion
        expected_percent = round(
            Decimal("58.0") * Decimal("0.09148") + Decimal("2.152"), 1
        )
        assert visit_data[0]["median_hba1c_percent"] == expected_percent

    def test_percent_format_conversion(self, setup_patients_and_visits):
        """Test HbA1c values in % format are correctly processed"""
        # Get the test data
        patient_data = setup_patients_and_visits
        patient_percent = patient_data["patient_percent"]
        audit_start, audit_end = audit_period_for_audit_year(patient_data["audit_year"])

        # Get visits using the function
        visits = get_median_hba1c_by_patient(
            audit_start=audit_start, audit_end=audit_end, patients=[patient_percent]
        )
        visit_data = list(visits)

        # Assertions
        assert len(visit_data) == 1
        assert visit_data[0]["median_hba1c_percent"] == Decimal("7.5")

        # Calculate expected HbA1c mmol/mol conversion
        expected_mmol_mol = round(
            (Decimal("7.5") - Decimal("2.152")) / Decimal("0.09148"), 2
        )

        assert visit_data[0]["median_hba1c_mmol_mol"] == expected_mmol_mol

    def test_eligibility_criteria(self, setup_patients_and_visits):
        """Test that visits must meet eligibility criteria"""
        # Get the test data
        patient_data = setup_patients_and_visits
        patient_mmol = patient_data["patient_mmol"]
        audit_start, audit_end = audit_period_for_audit_year(patient_data["audit_year"])

        # Get visits using the function
        visits = get_median_hba1c_by_patient(
            audit_start=audit_start, audit_end=audit_end, patients=[patient_mmol]
        )
        visit_data = list(visits)

        # Should only return 1 valid visit (excluding early_visit and null_hba1c_visit)
        assert len(visit_data) == 1
        # The visit should have HbA1c value 58.0 mmol/mol
        assert visit_data[0]["median_hba1c_mmol_mol"] == Decimal("58.0")

    def test_audit_year_filter(self, setup_patients_and_visits):
        """Test that visits are filtered by audit year"""
        # Get the test data
        patient_data = setup_patients_and_visits
        patient_mmol = patient_data["patient_mmol"]
        patient_prev_year = patient_data["patient_prev_year"]
        patient_next_year = patient_data["patient_next_year"]

        # Get visits for previous audit year
        audit_start, audit_end = audit_period_for_audit_year(
            patient_data["audit_year"] - 1
        )
        visits_prev_year = get_median_hba1c_by_patient(
            audit_start=audit_start, audit_end=audit_end, patients=[patient_prev_year]
        )
        visits_prev_year_data = list(visits_prev_year)

        # Get visits for current audit year
        audit_start, audit_end = audit_period_for_audit_year(patient_data["audit_year"])
        visits_current_year = get_median_hba1c_by_patient(
            audit_start=audit_start, audit_end=audit_end, patients=[patient_mmol]
        )
        visits_current_year_data = list(visits_current_year)

        # Get visits for next audit year
        audit_start, audit_end = audit_period_for_audit_year(
            patient_data["audit_year"] + 1
        )
        visits_next_year = get_median_hba1c_by_patient(
            audit_start=audit_start, audit_end=audit_end, patients=[patient_next_year]
        )
        visits_next_year_data = list(visits_next_year)

        # Assertions
        assert len(visits_prev_year_data) == 1
        assert visits_prev_year_data[0]["median_hba1c_mmol_mol"] == Decimal("55.0")

        assert len(visits_current_year_data) == 1
        assert visits_current_year_data[0]["median_hba1c_mmol_mol"] == Decimal("58.0")

        assert len(visits_next_year_data) == 1
        assert visits_next_year_data[0]["median_hba1c_mmol_mol"] == Decimal("52.0")

        # Check that no visits are returned for the wrong audit year
        audit_start, audit_end = audit_period_for_audit_year(
            patient_data["audit_year"] + 2
        )
        wrong_year_visits = get_median_hba1c_by_patient(
            audit_start=audit_start,
            audit_end=audit_end,
            patients=[patient_mmol, patient_prev_year, patient_next_year],
        )
        assert len(list(wrong_year_visits)) == 0

    def test_median_hba1c_mmol_mol_from_three_visits(self, setup_patients_and_visits):
        """Test median HbA1c calculation from three visits"""
        # Get the test data
        patient_data = setup_patients_and_visits
        patient_mmol = patient_data["patient_mmol"]
        audit_start, audit_end = audit_period_for_audit_year(patient_data["audit_year"])

        # Create additional visits for the same patient
        VisitFactory(
            patient=patient_mmol,
            visit_date=audit_start + timedelta(days=random.randint(30, 150)),
            hba1c_date=audit_start + timedelta(days=random.randint(30, 150)),
            hba1c=Decimal("60.0"),
            hba1c_format=HBA1C_FORMATS[0][0],  # mmol/mol
        )

        VisitFactory(
            patient=patient_mmol,
            visit_date=audit_start + timedelta(days=random.randint(30, 150)),
            hba1c_date=audit_start + timedelta(days=random.randint(30, 150)),
            hba1c=Decimal("62.0"),
            hba1c_format=HBA1C_FORMATS[0][0],  # mmol/mol
        )

        # Get visits using the function
        visits = get_median_hba1c_by_patient(
            audit_start=audit_start, audit_end=audit_end, patients=[patient_mmol]
        )
        visit_data = list(visits)

        # Assertions
        assert len(visit_data) == 1
        assert visit_data[0]["median_hba1c_mmol_mol"] == Decimal("60.0")

    def test_median_hba1c_percent_from_three_visits(self, setup_patients_and_visits):
        """Test median HbA1c calculation from three visits"""
        # Get the test data
        patient_data = setup_patients_and_visits
        patient_percent = patient_data["patient_percent"]
        audit_start, audit_end = audit_period_for_audit_year(patient_data["audit_year"])

        # Create additional visits for the same patient
        VisitFactory(
            patient=patient_percent,
            visit_date=audit_start + timedelta(days=random.randint(30, 150)),
            hba1c_date=audit_start + timedelta(days=random.randint(30, 150)),
            hba1c=Decimal("7.8"),
            hba1c_format=HBA1C_FORMATS[1][0],  # %
        )

        VisitFactory(
            patient=patient_percent,
            visit_date=audit_start + timedelta(days=random.randint(30, 150)),
            hba1c_date=audit_start + timedelta(days=random.randint(30, 150)),
            hba1c=Decimal("8.0"),
            hba1c_format=HBA1C_FORMATS[1][0],  # %
        )

        # Get visits using the function
        visits = get_median_hba1c_by_patient(
            audit_start=audit_start, audit_end=audit_end, patients=[patient_percent]
        )
        visit_data = list(visits)

        # Assertions
        assert len(visit_data) == 1
        assert visit_data[0]["median_hba1c_percent"] == Decimal("7.8")
